# Mundial - Juego de Pronósticos Copa del Mundo

> Mini juego web para adivinar los resultados de los partidos de la Copa del Mundo y competir por el primer lugar en el ranking.

## Características

- **Pronósticos en tiempo real**: Predice los resultados de los partidos antes de que inicien
- **Sistema de puntos dinámico**: Gana puntos según la precisión de tus pronósticos
- **Tabla de clasificación**: Compite con otros usuarios en el leaderboard general
- **Estadísticas detalladas**: Ricketts, exactos, precisión y más
- **Sincronización automática**: Los partidos se actualizan desde la API de football-data.org
- **Diseño responsive**: Interfaz limpia y moderna construida con Pico CSS

## Requisitos

- Python 3.10+
- Django 6.0
- API Key de [football-data.org](https://www.football-data.org)

## Instalación

1. **Clonar el repositorio**
```bash
git clone <repo-url>
cd mundial
```

2. **Crear y activar entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

3. **Instalar dependencias**
```bash
pip install django python-dotenv requests
```

4. **Configurar variables de entorno**

Crear archivo `.secret` en la raíz del proyecto:
```bash
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=tu-clave-secreta-aqui
FOOTBALL_DATA_API_KEY=tu-api-key-de-football-data
```

5. **Aplicar migraciones**
```bash
python manage.py migrate
```

6. **Crear superusuario (opcional)**
```bash
python manage.py createsuperuser
```

7. **Iniciar el servidor**
```bash
python manage.py runserver
```

8. **Sincronizar partidos y calcular puntos**
```bash
python manage.py sync_matches
python manage.py calculate_points
```

## Comandos de Gestión

| Comando | Descripción |
|---------|-------------|
| `python manage.py runserver` | Iniciar servidor de desarrollo |
| `python manage.py sync_matches` | Sincronizar partidos desde la API |
| `python manage.py calculate_points` | Calcular puntos de partidos finalizados |
| `python manage.py shell` | Abrir shell de Django |
| `python manage.py createsuperuser` | Crear administrador |

## Sistema de Puntos

| Resultado | Puntos | Descripción |
|-----------|--------|-------------|
| Marcador exacto | 3 pts | Acertar el resultado exacto (ej: 2-1) |
| Resultado | 2 pts | Acertar quién gana o si hay empate, pero no el marcador |
| Cantidad de goles de un equipo | 1 pt | Acertar la cantidad de goles de solo un equipo |

## Arquitectura

```
mundial/
├── core/                    # Configuración del proyecto Django
│   ├── settings.py
│   └── urls.py
├── worldcup/                # Aplicación principal
│   ├── models.py           # Match, Prediction, PlayerStats
│   ├── views.py            # Vistas y endpoints API
│   ├── services.py         # Cliente de API externa
│   └── management/commands/
│       ├── sync_matches.py
│       └── calculate_points.py
├── templates/              # Plantillas HTML
│   ├── base.html
│   ├── dashboard.html
│   ├── leaderboard.html
│   ├── match_detail.html
│   ├── profile.html
│   └── user_predictions.html
├── db.sqlite3              # Base de datos
├── manage.py
└── .secret                 # Variables de entorno (no commitear)
```

## API Externa

Este proyecto utiliza la API de [football-data.org](https://api.football-data.org/v4).

- Competencia: Copa del Mundo (código: `WC`)
- Endpoints principales:
  - Lista de partidos: `GET /v4/competitions/WC/matches`
  - Detalle de partido: `GET /v4/matches/{id}`

## Vistas Principales

| Ruta | Descripción |
|------|-------------|
| `/` | Dashboard con partidos próximos y completados |
| `/leaderboard/` | Tabla de clasificación general |
| `/matches/<id>/` | Detalle de un partido con pronósticos |
| `/predictions/` | Mis pronósticos |
| `/profile/` | Mi perfil y estadísticas |
| `/admin/` | Panel de administración Django |

## Tecnologías

- **Backend**: Django 6.0, Python 3.10+
- **Base de datos**: SQLite
- **Frontend**: HTML5, Pico CSS
- **API externa**: football-data.org
- **Gestión de configuración**: python-dotenv

## Licencia

MIT License