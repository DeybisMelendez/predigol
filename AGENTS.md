# Mundial - World Cup Guessing Game

## Project Type
Django 6.0 web application with SQLite database.

## Key Paths
- `manage.py` - Django management script
- `core/` - Project settings (settings.py, urls.py)
- `worldcup/` - Main app (models, views, services, management commands)
- `templates/` - HTML templates
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

# Sync matches from API
python manage.py sync_matches

# Calculate points for finished matches
python manage.py calculate_points

# Create superuser
python manage.py createsuperuser
```

## Architecture
- **Settings**: `core/settings.py` - Django project config
- **URLs**: `core/urls.py` includes `worldcup/urls`
- **Main App**: `worldcup/` contains:
  - `models.py` - Match and Prediction models
  - `views.py` - Dashboard, leaderboard, predictions
  - `services.py` - FootballDataAPI client
  - `management/commands/` - sync_matches, calculate_points

## External API
- Uses https://api.football-data.org/v4 (competition code: WC)
- API key stored in `.secret` as `FOOTBALL_DATA_API_KEY`