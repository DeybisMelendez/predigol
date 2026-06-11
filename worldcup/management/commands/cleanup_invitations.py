from django.core.management.base import BaseCommand
from django.utils import timezone
from worldcup.models import InvitationCode


class Command(BaseCommand):
    help = 'Delete expired invitation codes'

    def handle(self, *args, **options):
        deleted = InvitationCode.objects.filter(expires_at__lt=timezone.now()).delete()
        count = deleted[0]
        self.stdout.write(
            self.style.SUCCESS(f'Deleted {count} expired invitation codes')
        )