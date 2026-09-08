# Predigol - Multi-season football guessing game

## Project Type
Django 6.0 web application with SQLite database.

Two coexisting seasons:
- `worldcup` - Mundial 2026 (read-only, no further sync)
- `champions` - UEFA Champions League 2024-25+ (active)

## Key Paths
- `manage.py` - Django management script
- `core/` - Project settings (settings.py, urls.py)
- `worldcup/` - Mundial 2026 app (read-only mode)
- `champions/` - UEFA Champions League app (active)
- `templates/` - HTML templates for champions (root, active season)
- `templates/worldcup/` - HTML templates for worldcup (legacy season)
- `db.sqlite3` - SQLite database
- `.secret` - Environment variables (NOT `.env`)

## Environment Setup
Django settings loads env vars from `.secret` file (not `.env`):
```python
load_dotenv(dotenv_path=".secret")
```
Required keys in `.secret`:
- `DJANGO_DEBUG=True`
- `DJANGO_SECRET_KEY=...`
- `FOOTBALL_DATA_API_KEY=...` (from football-data.org)

## Developer Commands
```bash
# Run dev server
python manage.py runserver

# Run Django shell
python manage.py shell

# Apply migrations
python manage.py migrate

# Champions League (active season)
python manage.py sync_champions_matches
python manage.py calculate_champions_points

# Worldcup (read-only, no need to sync)
# python manage.py sync_matches
# python manage.py calculate_points

# Create superuser
python manage.py createsuperuser
```

## Architecture
- **Settings**: `core/settings.py` - Django project config
- **URLs**: `core/urls.py` includes both `worldcup` and `champions` namespaces
- **Worldcup App** (read-only):
  - `worldcup/models.py` - Match, Prediction (goles), PlayerStats
  - `worldcup/views.py` - Dashboard, leaderboard, predictions (marcador)
  - `worldcup/services.py` - FootballDataAPI client (competition="WC")
  - `worldcup/management/commands/` - sync_matches, calculate_points
- **Champions App** (active):
  - `champions/models.py` - Match, Prediction (1X2 + doble oportunidad), PlayerStats
  - `champions/views.py` - Dashboard, leaderboard, predictions, profile
  - `champions/services.py` - FootballDataAPI client (competition="CL")
  - `champions/stats.py` - Stats (aciertos 1X2 / doble oportunidad)
  - `champions/management/commands/` - sync_champions_matches, calculate_champions_points

## Scoring rules

### Champions (active)
- One selection per match from a group of 6 options (1, X, 2, 1X, X2, 12).
- 1X2 correct (1, X or 2): **3 pts**
- Double chance correct (1X, X2 or 12): **1 pt**
- No match: 0 pts.

### Worldcup (read-only, legacy)
- Exact score: 3 pts.
- Correct result: 2 pts.
- One team's goals correct: 1 pt.

## Routing
- Champions routes live at root (`/`, `/leaderboard/`, `/profile/`, `/match/<id>/`, `/api/predict/`, `/friends/...`) — esta es la temporada activa.
- Worldcup routes live under `/worldcup/` (e.g., `/worldcup/`, `/worldcup/leaderboard/`, `/worldcup/profile/`, `/worldcup/match/<id>/`, `/worldcup/api/predict/`, `/worldcup/friends/...`).
- After login users are redirected to `/`.
- Both `base.html` (champions at root and worldcup in `templates/worldcup/`) show a season switcher in the navbar to toggle between seasons.

## External API
Uses https://api.football-data.org/v4.
- Worldcup competition code: `WC` (legacy)
- Champions competition code: `CL`
- API key stored in `.secret` as `FOOTBALL_DATA_API_KEY`

## Friends & invitations
`Friendship` and `InvitationCode` models live in `worldcup.models` and are global (shared across seasons). Each season has its own leaderboard and stats.
