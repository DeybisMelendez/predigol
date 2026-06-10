import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta, timezone as tz
from zoneinfo import ZoneInfo
import time


def convert_utc_to_managua(utc_datetime_str):
    utc_dt = datetime.fromisoformat(utc_datetime_str.replace('Z', '+00:00'))
    managua_tz = ZoneInfo('America/Managua')
    managua_dt = utc_dt.astimezone(managua_tz)
    return managua_dt


class FootballDataAPI:
    BASE_URL = "https://api.football-data.org/v4"
    MAX_RETRIES = 3
    INITIAL_DELAY = 2

    def __init__(self):
        self.api_key = getattr(settings, 'FOOTBALL_DATA_API_KEY', None)
        if not self.api_key:
            raise ValueError("FOOTBALL_DATA_API_KEY not configured in settings")
        self.headers = {
            "X-Auth-Token": self.api_key
        }

    def _get(self, endpoint, params=None, _retries=0):
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 429:
                if _retries < self.MAX_RETRIES:
                    retry_after = int(response.headers.get('Retry-After', self.INITIAL_DELAY * (2 ** _retries)))
                    time.sleep(retry_after)
                    return self._get(endpoint, params, _retries + 1)
                raise Exception("Rate limit exceeded after retries")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if _retries < self.MAX_RETRIES:
                time.sleep(self.INITIAL_DELAY * (2 ** _retries))
                return self._get(endpoint, params, _retries + 1)
            raise

    def get_competition_matches(self, competition="WC", status=None, stage=None):
        params = {}
        if status:
            params["status"] = status
        if stage:
            params["stage"] = stage
        data = self._get(f"competitions/{competition}/matches", params)
        return data.get("matches", [])

    def get_match(self, match_id):
        return self._get(f"matches/{match_id}")

    def sync_matches_to_db(self):
        from .models import Match
        matches = self.get_competition_matches(competition="WC")
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for match_data in matches:
            try:
                match_id_ext = match_data["id"]

                home_team_data = match_data.get("homeTeam") or {}
                away_team_data = match_data.get("awayTeam") or {}
                home_team = home_team_data.get("name")
                away_team = away_team_data.get("name")
                home_team_crest = home_team_data.get("crest")
                away_team_crest = away_team_data.get("crest")

                if not home_team or not away_team:
                    skipped_count += 1
                    continue
                datetime_str = match_data["utcDate"]
                converted_datetime = convert_utc_to_managua(datetime_str)
                stage = match_data["stage"]
                group = match_data.get("group")
                status = match_data["status"]

                home_score = None
                away_score = None
                if "score" in match_data and match_data["score"].get("fullTime"):
                    home_score = match_data["score"]["fullTime"].get("home")
                    away_score = match_data["score"]["fullTime"].get("away")

                goals = match_data.get("goals", [])
                bookings = match_data.get("bookings", [])
                substitutions = match_data.get("substitutions", [])
                home_lineup = home_team_data.get("lineup", [])
                away_lineup = away_team_data.get("lineup", [])
                home_bench = home_team_data.get("bench", [])
                away_bench = away_team_data.get("bench", [])
                home_coach = home_team_data.get("coach", {}).get("name") if home_team_data.get("coach") else None
                away_coach = away_team_data.get("coach", {}).get("name") if away_team_data.get("coach") else None
                home_formation = home_team_data.get("formation")
                away_formation = away_team_data.get("formation")
                home_formation = home_team_data.get("formation")
                away_formation = away_team_data.get("formation")
                venue = match_data.get("venue")
                attendance = match_data.get("attendance")
                injury_time = match_data.get("injuryTime")
                referees = match_data.get("referees", [])

                match, created = Match.objects.update_or_create(
                    match_id_externo=match_id_ext,
                    defaults={
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_team_crest": home_team_crest,
                        "away_team_crest": away_team_crest,
                        "datetime": converted_datetime,
                        "stage": stage,
                        "group": group,
                        "status": status,
                        "home_score": home_score,
                        "away_score": away_score,
                        "home_lineup": home_lineup,
                        "away_lineup": away_lineup,
                        "goals": goals,
                        "bookings": bookings,
                        "substitutions": substitutions,
                        "home_lineup": home_lineup,
                        "away_lineup": away_lineup,
                        "home_bench": home_bench,
                        "away_bench": away_bench,
                        "home_coach": home_coach,
                        "away_coach": away_coach,
                        "home_formation": home_formation,
                        "away_formation": away_formation,
                        "venue": venue,
                        "attendance": attendance,
                        "injury_time": injury_time,
                        "referees": referees,
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                import traceback
                print(f"Error syncing match {match_data.get('id')}: {e}")
                print(f"  homeTeam: {match_data.get('homeTeam')}")
                print(f"  awayTeam: {match_data.get('awayTeam')}")
                print(f"  status: {match_data.get('status')}")
                print(f"  trace: {traceback.format_exc()[:200]}")

        return created_count, updated_count, skipped_count

    def _get_match_update_data(self, match_data):
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

        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_team_crest": home_team_data.get("crest"),
            "away_team_crest": away_team_data.get("crest"),
            "datetime": convert_utc_to_managua(match_data["utcDate"]),
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
            return None
        match, created = Match.objects.update_or_create(
            match_id_externo=match_id_ext,
            defaults=update_data
        )
        return match, created

    def sync_match_if_needed(self, match_id):
        from .models import Match
        try:
            match = Match.objects.get(id=match_id)
        except Match.DoesNotExist:
            return None

        if match.status in ['FINISHED', 'CANCELLED', 'POSTPONED', 'SUSPENDED']:
            return None

        cache_key = f"match_sync_{match.match_id_externo}"
        last_sync = cache.get(cache_key)
        should_sync = last_sync is None

        if not should_sync:
            from django.utils import timezone
            elapsed = timezone.now() - last_sync
            should_sync = elapsed >= timedelta(minutes=5)

        if not should_sync:
            return None

        try:
            api_data = self.get_match(match.match_id_externo)
            result = self.sync_match(api_data)
            cache.set(cache_key, timezone.now(), timeout=300)
            return result
        except Exception as e:
            print(f"Error syncing match {match_id}: {e}")
            return None

    def sync_active_matches(self):
        from .models import Match, Prediction

        cache_key = "last_global_sync"
        last_sync = cache.get(cache_key)
        should_sync = last_sync is None

        if not should_sync:
            elapsed = timezone.now() - last_sync
            should_sync = elapsed >= timedelta(minutes=5)

        if not should_sync:
            return 0, 0

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
                print(f"Error syncing match {match_data.get('id')}: {e}")

        if finished_matches_to_update:
            points_updated = self._calculate_points_for_matches(finished_matches_to_update)
            synced_count += points_updated

        cache.set(cache_key, timezone.now(), timeout=300)
        return len(all_matches), synced_count

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