from django.core.management.base import BaseCommand
from worldcup.services import FootballDataAPI, BATCH_DELAY


class Command(BaseCommand):
    help = 'Synchronize matches from football-data.org API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of matches to process before waiting (default: 10)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=BATCH_DELAY,
            help=f'Delay in seconds between batches (default: {BATCH_DELAY})'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sync even if recently synced'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        delay = options['delay']
        force = options['force']

        self.stdout.write(f'Starting match synchronization (batch_size={batch_size}, delay={delay}s)...')
        try:
            api = FootballDataAPI()
            created, updated, skipped = api.sync_matches_to_db(
                batch_size=batch_size,
                delay_between_batches=delay
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully synchronized: {created} created, {updated} updated, {skipped} skipped'
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error syncing matches: {e}'))