#!/usr/bin/env python
"""
Script standalone para ejecutar desde PythonAnywhere (scheduler hourly).
Sincroniza partidos de la API y calcula puntos de predicciones.

Uso desde PythonAnywhere:
    python /path/to/mundial/run_hourly_tasks.py
"""
import os
import sys
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from worldcup.services import FootballDataAPI
from worldcup.models import Match, Prediction, PlayerStats


def sync_matches():
    logger.info("=" * 50)
    logger.info("Iniciando sincronizacion de partidos...")
    try:
        api = FootballDataAPI()
        created, updated, skipped = api.sync_matches_to_db(batch_size=10, delay_between_batches=6)
        logger.info(f"Sync completado: {created} creados, {updated} actualizados, {skipped} omitidos")
        return True
    except Exception as e:
        logger.error(f"Error en sync_matches: {e}")
        return False


def calculate_points():
    logger.info("=" * 50)
    logger.info("Calculando puntos de predicciones...")
    updated_count = 0

    finished_matches = Match.objects.filter(status='FINISHED')

    for match in finished_matches:
        predictions = Prediction.objects.filter(match=match)
        for prediction in predictions:
            old_points = prediction.points
            prediction.calculate_points()
            if old_points != prediction.points:
                updated_count += 1

    logger.info(f"Puntos actualizados para {updated_count} predicciones")

    update_player_stats()
    logger.info("PlayerStats actualizados")


def update_player_stats():
    users_with_predictions = Prediction.objects.values('user').distinct()

    for user_data in users_with_predictions:
        user_id = user_data['user']
        predictions = Prediction.objects.filter(user_id=user_id, match__status='FINISHED')

        total = predictions.count()
        if total == 0:
            continue

        exact = predictions.filter(points=3).count()
        winner = predictions.filter(points=2).count()
        goals = predictions.filter(points=1).count()

        correct = exact + winner + goals
        accuracy = round((correct / total) * 100, 1)

        current_streak, longest_streak = calculate_streaks(predictions.order_by('match__datetime'))

        stats, created = PlayerStats.objects.get_or_create(user_id=user_id)
        stats.total_predictions = total
        stats.exact_count = exact
        stats.winner_count = winner
        stats.goals_count = goals
        stats.accuracy = accuracy
        stats.current_streak = current_streak
        stats.longest_streak = longest_streak
        stats.save()

        status = 'creado' if created else 'actualizado'
        logger.info(f"PlayerStats {status} para usuario {user_id}")


def calculate_streaks(predictions):
    current_streak = 0
    longest_streak = 0
    temp_streak = 0

    for pred in predictions:
        if pred.points > 0:
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0

    current_streak = temp_streak
    return current_streak, longest_streak


def main():
    start_time = datetime.now()
    logger.info("=" * 50)
    logger.info("INICIO - run_hourly_tasks")
    logger.info("=" * 50)

    sync_ok = sync_matches()
    if sync_ok:
        calculate_points()
    else:
        logger.warning("Sincronizacion fallida, omitiendo calculo de puntos")

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("=" * 50)
    logger.info(f"FIN - Tarea completada en {elapsed:.1f} segundos")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()