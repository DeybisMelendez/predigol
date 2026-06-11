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
from worldcup.models import Prediction, PlayerStats


def sync_matches():
    logger.info("=" * 50)
    logger.info("Iniciando sincronizacion de partidos...")
    logger.info("Obteniendo partidos desde la API de football-data...")
    try:
        api = FootballDataAPI()
        logger.info("API inicializada, comenzando sync...")
        created, updated, skipped = api.sync_matches_to_db(batch_size=10, delay_between_batches=6)

        logger.info("-" * 50)
        logger.info("RESULTADO DE SINCRONIZACION:")
        logger.info("  - Partidos creados (nuevos): %d", created)
        logger.info("  - Partidos actualizados: %d", updated)
        logger.info("  - Partidos omitidos (sin datos validos): %d", skipped)
        logger.info("-" * 50)

        total_synced = created + updated
        logger.info("Total de partidos sincronizados: %d", total_synced)

        from worldcup.models import Match
        total_matches = Match.objects.count()
        logger.info("Total de partidos en base de datos: %d", total_matches)

        finished = Match.objects.filter(status='FINISHED').count()
        scheduled = Match.objects.filter(status__in=['SCHEDULED', 'TIMED']).count()
        in_play = Match.objects.filter(status__in=['IN_PLAY', 'PAUSED']).count()

        logger.info("Estado de partidos:")
        logger.info("  - Terminados (FINISHED): %d", finished)
        logger.info("  - Programados (SCHEDULED/TIMED): %d", scheduled)
        logger.info("  - En juego (IN_PLAY/PAUSED): %d", in_play)

        return True
    except Exception as e:
        logger.error("Error en sync_matches: %s", e)
        import traceback
        logger.error("Traceback: %s", traceback.format_exc())
        return False


def calculate_points():
    logger.info("=" * 50)
    logger.info("Calculando puntos de predicciones...")

    from worldcup.models import Match, Prediction

    finished_matches = Match.objects.filter(status='FINISHED')
    total_finished = finished_matches.count()

    logger.info("Partidos terminados encontrados: %d", total_finished)

    if total_finished == 0:
        logger.info("No hay partidos terminados, no se calculan puntos")
        update_player_stats()
        logger.info("PlayerStats actualizados")
        return

    updated_count = 0
    updated_predictions_details = []

    for match in finished_matches:
        predictions = Prediction.objects.filter(match=match)
        total_preds = predictions.count()
        logger.info("Procesando partido %s: %d predicciones", match, total_preds)

        for prediction in predictions:
            old_points = prediction.points
            prediction.calculate_points()
            if old_points != prediction.points:
                updated_count += 1
                updated_predictions_details.append({
                    'user': prediction.user_id,
                    'match': str(match),
                    'old': old_points,
                    'new': prediction.points
                })

    logger.info("-" * 50)
    logger.info("RESULTADO DE CALCULO DE PUNTOS:")
    logger.info("  - Total predicciones actualizadas: %d", updated_count)
    logger.info("-" * 50)

    if updated_predictions_details:
        logger.info("Detalle de predicciones actualizadas:")
        for detail in updated_predictions_details[:10]:
            logger.info("  Usuario %s | Partido %s | %d -> %d puntos",
                       detail['user'], detail['match'], detail['old'], detail['new'])
        if len(updated_predictions_details) > 10:
            logger.info("  ... y %d mas", len(updated_predictions_details) - 10)

    update_player_stats()
    logger.info("PlayerStats actualizados")


def update_player_stats():
    users_with_predictions = Prediction.objects.values('user').distinct()
    total_users = len(users_with_predictions)
    logger.info("Actualizando PlayerStats para %d usuarios...", total_users)

    stats_created = 0
    stats_updated = 0

    for user_data in users_with_predictions:
        user_id = user_data['user']
        predictions = Prediction.objects.filter(user_id=user_id, match__status='FINISHED')

        total = predictions.count()
        if total == 0:
            logger.debug("Usuario %d: sin predicciones en partidos terminados, saltando", user_id)
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

        if created:
            stats_created += 1
        else:
            stats_updated += 1

        logger.debug("Usuario %d: total=%d, exactos=%d, ganador=%d, goles=%d, accuracy=%.1f%%, streak=%d/%d",
                    user_id, total, exact, winner, goals, accuracy, current_streak, longest_streak)

    logger.info("-" * 50)
    logger.info("RESULTADO DE PLAYERSTATS:")
    logger.info("  - Stats creados: %d", stats_created)
    logger.info("  - Stats actualizados: %d", stats_updated)
    logger.info("-" * 50)


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
    logger.info("FIN - Tarea completada en %.1f segundos", elapsed)
    logger.info("=" * 50)


if __name__ == "__main__":
    main()