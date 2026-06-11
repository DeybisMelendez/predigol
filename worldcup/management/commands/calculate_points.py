from django.core.management.base import BaseCommand
from worldcup.models import Match, Prediction, PlayerStats


class Command(BaseCommand):
    help = 'Calculate points for predictions based on finished matches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--uncalculated-only',
            action='store_true',
            default=True,
            help='Only update predictions with points=0 (default: True)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Recalculate all predictions regardless of current points'
        )
        parser.add_argument(
            '--match-id',
            type=int,
            help='Only calculate points for a specific match ID'
        )

    def handle(self, *args, **options):
        uncalculated_only = options.get('uncalculated_only', True)
        recalculate_all = options.get('all', False)
        match_id = options.get('match_id')

        if recalculate_all:
            uncalculated_only = False

        query = Match.objects.filter(status='FINISHED')
        if match_id:
            query = query.filter(id=match_id)

        finished_matches = query
        updated_count = 0

        for match in finished_matches:
            pred_query = Prediction.objects.filter(match=match)
            if uncalculated_only and not recalculate_all:
                pred_query = pred_query.filter(points=0)

            for prediction in pred_query:
                old_points = prediction.points
                prediction.calculate_points()
                if old_points != prediction.points:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Points calculated for {updated_count} predictions')
        )

        self.update_player_stats()

    def update_player_stats(self):
        users_with_predictions = Prediction.objects.values('user').distinct()

        for user_data in users_with_predictions:
            user_id = user_data['user']
            predictions = Prediction.objects.filter(user_id=user_id, match__status='FINISHED')

            total_points = sum(p.points for p in predictions)

            stats, created = PlayerStats.objects.get_or_create(user_id=user_id)
            stats.total_points = total_points
            stats.save()

            status = 'created' if created else 'updated'
            self.stdout.write(f'PlayerStats {status} for user {user_id}: total_points={total_points}')