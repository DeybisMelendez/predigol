from django.contrib.auth.models import User
from django.db.models import Sum

from .models import Prediction


def compute_user_stats(user):
    """Calcula las estadisticas de rendimiento de un usuario a partir de sus
    pronosticos. Solo los partidos finalizados se consideran para los
    porcentajes de acierto; los pendientes se reportan por separado."""
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

    exact_hits = sum(1 for p in finished if p.points == 3)
    result_hits = sum(1 for p in finished if p.points == 2)
    one_goal_hits = sum(1 for p in finished if p.points == 1)
    missed = sum(1 for p in finished if p.points == 0)

    total_points = sum(p.points for p in finished)
    avg_points = (total_points / finished_count) if finished_count else 0.0

    winner_matches = [p for p in finished if p.match._get_result() in ('H', 'A')]
    draw_matches = [p for p in finished if p.match._get_result() == 'D']
    winner_hits = sum(
        1 for p in winner_matches if p._get_result() == p.match._get_result()
    )
    draw_hits = sum(1 for p in draw_matches if p._get_result() == 'D')

    winner_accuracy = (winner_hits / len(winner_matches) * 100) if winner_matches else None
    draw_accuracy = (draw_hits / len(draw_matches) * 100) if draw_matches else None
    exact_accuracy = (exact_hits / finished_count * 100) if finished_count else None

    current_streak, best_streak = _compute_streaks(finished)

    return {
        'total_points': total_points,
        'total_predictions': total_predictions,
        'pending_predictions': len(pending),
        'finished_predictions': finished_count,
        'exact_hits': exact_hits,
        'result_hits': result_hits,
        'one_goal_hits': one_goal_hits,
        'missed': missed,
        'avg_points': avg_points,
        'winner_accuracy': winner_accuracy,
        'draw_accuracy': draw_accuracy,
        'exact_accuracy': exact_accuracy,
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
        'exact_hits': 0,
        'result_hits': 0,
        'one_goal_hits': 0,
        'missed': 0,
        'avg_points': 0.0,
        'winner_accuracy': None,
        'draw_accuracy': None,
        'exact_accuracy': None,
        'current_streak': 0,
        'best_streak': 0,
        'has_finished': False,
    }


def get_ranking_position(user):
    """Devuelve (posicion, total_usuarios) del usuario en el ranking global.
    Si el usuario no tiene pronosticos, la posicion es None."""
    ranked = list(
        User.objects
        .filter(prediction__isnull=False)
        .annotate(total_points=Sum('prediction__points'))
        .order_by('-total_points')
        .values_list('id', flat=True)
    )
    total_users = len(ranked)
    if user.id not in ranked:
        return None, total_users
    return ranked.index(user.id) + 1, total_users
