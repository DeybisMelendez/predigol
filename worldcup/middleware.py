import logging
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

logger = logging.getLogger(__name__)

SYNC_LOCK_KEY = "middleware_sync_lock"
SYNC_LOCK_TIMEOUT = 30


class SyncOnAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.SYNC_INTERVAL = timedelta(minutes=5)

    def __call__(self, request):
        if request.user.is_authenticated:
            self._sync_if_needed(request)

        return self.get_response(request)

    def _sync_if_needed(self, request):
        lock_acquired = cache.add(SYNC_LOCK_KEY, timezone.now().isoformat(), SYNC_LOCK_TIMEOUT)
        if not lock_acquired:
            logger.debug("Sync already in progress, skipping")
            return

        try:
            from .services import FootballDataAPI
            api = FootballDataAPI()
            api.sync_active_matches()
        except Exception as e:
            logger.exception("Error in passive sync: %s", e)
        finally:
            cache.delete(SYNC_LOCK_KEY)