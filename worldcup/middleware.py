from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta


class SyncOnAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.SYNC_INTERVAL = timedelta(minutes=5)

    def __call__(self, request):
        if request.user.is_authenticated:
            self._sync_if_needed(request)

        return self.get_response(request)

    def _sync_if_needed(self, request):
        cache_key = "last_global_sync"
        last_sync = cache.get(cache_key)

        if last_sync is None:
            should_sync = True
        else:
            elapsed = timezone.now() - last_sync
            should_sync = elapsed >= self.SYNC_INTERVAL

        if should_sync:
            try:
                from .services import FootballDataAPI
                api = FootballDataAPI()
                api.sync_active_matches()
            except Exception as e:
                print(f"Error in passive sync: {e}")