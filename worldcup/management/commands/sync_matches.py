from django.core.management.base import BaseCommand
from worldcup.services import FootballDataAPI


class Command(BaseCommand):
    help = 'Synchronize matches from football-data.org API'

    def handle(self, *args, **options):
        self.stdout.write('Starting match synchronization...')
        try:
            api = FootballDataAPI()
            created, updated, skipped = api.sync_matches_to_db()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully synchronized: {created} created, {updated} updated, {skipped} skipped (no teams yet)')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error syncing matches: {e}')
            )