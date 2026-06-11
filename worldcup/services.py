import requests
import logging
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta, datetime
from dotenv import load_dotenv
import time
import os


load_dotenv(dotenv_path=str(settings.BASE_DIR / ".secret"))
logger = logging.getLogger(__name__)

RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW = 60
SYNC_CACHE_KEY = "last_global_sync"
SYNC_LOCK_KEY = "sync_in_progress"
SYNC_LOCK_TIMEOUT = 120
MIN_SYNC_INTERVAL = timedelta(minutes=5)
BATCH_DELAY = 6


class RateLimitTracker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.requests = []
            cls._instance.lock = __import__('threading').Lock()
        return cls._instance

    def can_make_request(self):
        with self.lock:
            now = time.time()
            self.requests = [t for t in self.requests if now - t < RATE_LIMIT_WINDOW]
            return len(self.requests) < RATE_LIMIT_REQUESTS

    def record_request(self):
        with self.lock:
            self.requests.append(time.time())

    def time_until_next_slot(self):
        with self.lock:
            if len(self.requests) < RATE_LIMIT_REQUESTS:
                return 0
            oldest = min(self.requests)
            return max(0, RATE_LIMIT_WINDOW - (time.time() - oldest))


class FootballDataAPI:
    BASE_URL = "https://api.football-data.org/v4"
    MAX_RETRIES = 2
    INITIAL_DELAY = 2

    def __init__(self):
        from django.conf import settings
        self.api_key = os.environ.get("FOOTBALL_DATA_API_KEY")
        logger.info(f"FootballDataAPI init - API key: {'OK' if self.api_key else 'VACIA/NONE'}")
        self.headers = {"X-Auth-Token": self.api_key}
        self.rate_tracker = RateLimitTracker()

    def _wait_for_rate_limit(self):
        while not self.rate_tracker.can_make_request():
            wait_time = self.rate_tracker.time_until_next_slot()
            if wait_time > 0:
                logger.debug("Rate limit approaching, waiting %.1f seconds", wait_time)
                time.sleep(min(wait_time, BATCH_DELAY))

    def _get(self, endpoint, params=None, _retries=0):
        self._wait_for_rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"
        logger.debug(f"GET {url} | API key: {self.api_key[:4]}...{self.api_key[-4:] if self.api_key else 'NONE'}")
        try:
            response = requests.get(url, headers=self.headers, params=params)
            self.rate_tracker.record_request()

            if response.status_code == 429:
                logger.warning("Rate limit hit (429) on %s", endpoint)
                if _retries < self.MAX_RETRIES:
                    retry_after = int(response.headers.get('Retry-After', BATCH_DELAY))
                    logger.info("Retrying after %d seconds (attempt %d/%d)", retry_after, _retries + 1, self.MAX_RETRIES)
                    time.sleep(retry_after)
                    return self._get(endpoint, params, _retries + 1)
                raise Exception("Rate limit exceeded after retries")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            if _retries < self.MAX_RETRIES:
                delay = self.INITIAL_DELAY * (2 ** _retries)
                logger.warning("Request failed, retrying in %d seconds: %s", delay, e)
                time.sleep(delay)
                return self._get(endpoint, params, _retries + 1)
            logger.error("Request failed after %d retries: %s", self.MAX_RETRIES, e)
            raise

    def get_competition_matches(self, competition="WC", status=None, stage=None):
        params = {}
        if status:
            params["status"] = status
        if stage:
            params["stage"] = stage
        logger.info("Fetching competition matches for %s", competition)
        data = self._get(f"competitions/{competition}/matches", params)
        matches = data.get("matches", [])
        logger.info("Fetched %d matches from API", len(matches))
        return matches

    def get_match(self, match_id):
        return self._get(f"matches/{match_id}")

    def _get_match_update_data(self, match_data):
        from datetime import datetime as dt
        home_team_data = match_data.get("homeTeam") or {}
        away_team_data = match_data.get("awayTeam") or {}
        home_team = home_team_data.get("name")
        away_team = away_team_data.get("name")

        if not home_team or not away_team:
            return None

        home_score = None
        away_score = None
        if "score" in match_data and match_data["score"].get("fullTime"):
            home_score = match_data["score"]["fullTime"].get("home")
            away_score = match_data["score"]["fullTime"].get("away")

        if home_score is None and away_score is None and match_data.get("status") == "FINISHED":
            logger.info("Score is None for FINISHED match %s, fetching fresh data", match_data.get("id"))
            try:
                fresh_data = self.get_match(match_data["id"])
                if fresh_data:
                    fresh_score = fresh_data.get("score", {})
                    home_score = fresh_score.get("fullTime", {}).get("home")
                    away_score = fresh_score.get("fullTime", {}).get("away")
                    logger.info("Fresh scores for match %s: %s-%s", match_data.get("id"), home_score, away_score)
            except Exception as e:
                logger.error("Error fetching fresh score for match %s: %s", match_data.get("id"), e)

        datetime_str = match_data["utcDate"]
        utc_dt = dt.fromisoformat(datetime_str.replace('Z', '+00:00'))
        converted_datetime = utc_dt.replace(tzinfo=timezone.UTC)

        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_team_crest": home_team_data.get("crest"),
            "away_team_crest": away_team_data.get("crest"),
            "datetime": converted_datetime,
            "stage": match_data["stage"],
            "group": match_data.get("group"),
            "status": match_data["status"],
            "home_score": home_score,
            "away_score": away_score,
            "goals": match_data.get("goals", []),
            "bookings": match_data.get("bookings", []),
            "substitutions": match_data.get("substitutions", []),
            "home_lineup": home_team_data.get("lineup", []),
            "away_lineup": away_team_data.get("lineup", []),
            "home_bench": home_team_data.get("bench", []),
            "away_bench": away_team_data.get("bench", []),
            "home_coach": home_team_data.get("coach", {}).get("name") if home_team_data.get("coach") else None,
            "away_coach": away_team_data.get("coach", {}).get("name") if away_team_data.get("coach") else None,
            "home_formation": home_team_data.get("formation"),
            "away_formation": away_team_data.get("formation"),
            "venue": match_data.get("venue"),
            "attendance": match_data.get("attendance"),
            "injury_time": match_data.get("injuryTime"),
            "referees": match_data.get("referees", []),
        }

    def sync_match(self, match_data):
        from .models import Match
        match_id_ext = match_data["id"]
        update_data = self._get_match_update_data(match_data)
        if not update_data:
            return None, None

        existing_match = Match.objects.filter(match_id_externo=match_id_ext).first()
        if existing_match and existing_match.status == 'FINISHED':
            if existing_match.home_score is not None and existing_match.away_score is not None:
                if update_data.get('home_score') is None and update_data.get('away_score') is None:
                    logger.info("Preserving manual scores for FINISHED match %s: %s-%s",
                               match_id_ext, existing_match.home_score, existing_match.away_score)
                    update_data.pop('home_score', None)
                    update_data.pop('away_score', None)

        match, created = Match.objects.update_or_create(
            match_id_externo=match_id_ext,
            defaults=update_data
        )
        return match, created

    def sync_active_matches(self, force=False):
        from .models import Match, Prediction

        cache_key = SYNC_CACHE_KEY
        last_sync = cache.get(cache_key)
        should_sync = last_sync is None

        if not should_sync:
            elapsed = timezone.now() - last_sync
            should_sync = force or elapsed >= MIN_SYNC_INTERVAL

        if not should_sync:
            logger.debug("Sync skipped: elapsed time %.1f min < %.1f min", elapsed.total_seconds() / 60, MIN_SYNC_INTERVAL.total_seconds() / 60)
            return 0, 0

        lock_value = cache.get(SYNC_LOCK_KEY)
        if lock_value:
            try:
                lock_time = datetime.fromisoformat(lock_value)
                lock_age = (timezone.now() - lock_time).total_seconds()
                if lock_age < SYNC_LOCK_TIMEOUT:
                    logger.debug("Sync locked by another process (age: %.1f s)", lock_age)
                    return 0, 0
                logger.info("Stale lock found (age: %.1f s), will override", lock_age)
            except (TypeError, ValueError):
                pass

        cache.set(SYNC_LOCK_KEY, timezone.now().isoformat(), SYNC_LOCK_TIMEOUT)

        try:
            all_matches = self.get_competition_matches(competition="WC")
            synced_count = 0
            finished_matches_to_update = []

            for match_data in all_matches:
                status = match_data.get("status")
                if status not in ['SCHEDULED', 'TIMED', 'IN_PLAY', 'PAUSED', 'FINISHED']:
                    continue

                try:
                    result = self.sync_match(match_data)
                    if result:
                        _, created = result
                        if not created:
                            synced_count += 1

                        match_id_ext = match_data.get("id")
                        match = Match.objects.filter(match_id_externo=match_id_ext).first()
                        if match and match.status == 'FINISHED' and match.home_score is not None:
                            finished_matches_to_update.append(match)
                except Exception as e:
                    logger.error("Error syncing match %s: %s", match_data.get('id'), e)

            if finished_matches_to_update:
                points_updated = self._calculate_points_for_matches(finished_matches_to_update)
                logger.info("Updated points for %d finished matches", points_updated)
                synced_count += points_updated

            cache.set(cache_key, timezone.now(), timeout=int(MIN_SYNC_INTERVAL.total_seconds()))
            logger.info("Sync completed: %d matches updated", synced_count)
            return len(all_matches), synced_count

        except Exception as e:
            logger.exception("Sync failed: %s", e)
            raise
        finally:
            cache.delete(SYNC_LOCK_KEY)

    def _calculate_points_for_matches(self, matches):
        from .models import Prediction
        updated_count = 0
        for match in matches:
            predictions = Prediction.objects.filter(match=match, points=0)
            for pred in predictions:
                old_points = pred.points
                pred.calculate_points()
                if old_points != pred.points:
                    updated_count += 1
        return updated_count

    def sync_matches_to_db(self, batch_size=10, delay_between_batches=BATCH_DELAY):
        from .models import Match
        matches = self.get_competition_matches(competition="WC")
        total_matches = len(matches)
        created_count = 0
        updated_count = 0
        skipped_count = 0

        logger.info("Starting full sync of %d matches (batch_size=%d, delay=%.1fs)", total_matches, batch_size, delay_between_batches)

        for i, match_data in enumerate(matches):
            try:
                match_id_ext = match_data["id"]
                update_data = self._get_match_update_data(match_data)

                if not update_data:
                    skipped_count += 1
                    continue

                match, created = Match.objects.update_or_create(
                    match_id_externo=match_id_ext,
                    defaults=update_data
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

                if (i + 1) % batch_size == 0 and i + 1 < total_matches:
                    logger.debug("Processed %d/%d matches, waiting %.1fs for rate limit", i + 1, total_matches, delay_between_batches)
                    time.sleep(delay_between_batches)

            except Exception as e:
                logger.error("Error syncing match %s: %s", match_data.get('id'), e)

        logger.info("Full sync completed: created=%d, updated=%d, skipped=%d", created_count, updated_count, skipped_count)
        return created_count, updated_count, skipped_count

    def sync_match_by_id(self, match_id):
        try:
            api_data = self.get_match(match_id)
            return self.sync_match(api_data)
        except Exception as e:
            logger.error("Error syncing match %s by ID: %s", match_id, e)
            return None, None