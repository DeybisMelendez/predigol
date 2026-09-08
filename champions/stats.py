from django.contrib.auth.models import User
from django.db.models import Sum

from .models import Prediction, PlayerStats


def compute_user_stats(user):
    """Calcula las estadisticas de rendimiento de un usuario a partir de sus
    pronosticos en Champions. Solo los partidos finalizados se consideran para
    los porcentajes de acierto; los pendientes se reportan por separado."""
    predictions = list(
        Prediction.objects
        .filter(user=user)
        .select_related('match')
        .order_by('match__datetime')
    )

    total_predictions = len(predictions)
    if total_predictions == 0:
        return _empty_stats()

    finished = [p for p in predictions if p.match.is_finished]
    pending = [p for p in predictions if not p.match.is_finished]
    finished_count = len(finished)

    pick_hits_3pts = sum(1 for p in finished if p.is_1x2 and p.points == 3)
    pick_misses_3pts = sum(1 for p in finished if p.is_1x2 and p.points == 0)
    double_chance_hits = sum(1 for p in finished if p.is_double_chance and p.points == 1)
    double_chance_misses = sum(1 for p in finished if p.is_double_chance and p.points == 0)

    total_1x2 = pick_hits_3pts + pick_misses_3pts
    total_dc = double_chance_hits + double_chance_misses

    total_points = sum(p.points for p in finished)
    avg_points = (total_points / finished_count) if finished_count else 0.0

    pick_3pt_accuracy = (pick_hits_3pts / total_1x2 * 100) if total_1x2 else None
    double_chance_accuracy = (double_chance_hits / total_dc * 100) if total_dc else None

    current_streak, best_streak = _compute_streaks(finished)

    return {
        'total_points': total_points,
        'total_predictions': total_predictions,
        'pending_predictions': len(pending),
        'finished_predictions': finished_count,
        'pick_hits_3pts': pick_hits_3pts,
        'pick_misses_3pts': pick_misses_3pts,
        'double_chance_hits': double_chance_hits,
        'double_chance_misses': double_chance_misses,
        'avg_points': avg_points,
        'pick_3pt_accuracy': pick_3pt_accuracy,
        'double_chance_accuracy': double_chance_accuracy,
        'current_streak': current_streak,
        'best_streak': best_streak,
        'has_finished': finished_count > 0,
    }


def _compute_streaks(finished):
    """Racha de aciertos consecutivos (puntos > 0) sobre partidos finalizados
    ordenados cronologicamente."""
    best = 0
    running = 0
    for p in finished:
        if p.points > 0:
            running += 1
            best = max(best, running)
        else:
            running = 0

    current = 0
    for p in reversed(finished):
        if p.points > 0:
            current += 1
        else:
            break
    return current, best


def _empty_stats():
    return {
        'total_points': 0,
        'total_predictions': 0,
        'pending_predictions': 0,
        'finished_predictions': 0,
        'pick_hits_3pts': 0,
        'pick_misses_3pts': 0,
        'double_chance_hits': 0,
        'double_chance_misses': 0,
        'avg_points': 0.0,
        'pick_3pt_accuracy': None,
        'double_chance_accuracy': None,
        'current_streak': 0,
        'best_streak': 0,
        'has_finished': False,
    }


def get_ranking_position(user):
    """Devuelve (posicion, total_usuarios) del usuario en el ranking UCL.
    Si el usuario no tiene pronosticos en champions, la posicion es None."""
    ranked = list(
        User.objects
        .filter(champions_predictions__isnull=False)
        .annotate(total_points=Sum('champions_predictions__points'))
        .order_by('-total_points')
        .values_list('id', flat=True)
    )
    total_users = len(ranked)
    if user.id not in ranked:
        return None, total_users
    return ranked.index(user.id) + 1, total_users
