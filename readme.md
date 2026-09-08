# Predigol - Juego de Pronósticos Multi-Temporada

> Mini juego web para adivinar los resultados de los partidos de fútbol y competir por el primer lugar en el ranking. Soporta múltiples temporadas (Mundial 2026, UEFA Champions League) coexistiendo.

## Características

- **Dos temporadas activas**: Mundial 2026 (lectura) y UEFA Champions League (activa).
- **Pronósticos en tiempo real**: Predice antes de que inicien los partidos.
- **Sistema de puntos dinámico**:
  - Champions: 1X2 (3 pts) y doble oportunidad (1 pt).
  - Worldcup: marcador exacto (3), resultado (2), goles de un equipo (1).
- **Tabla de clasificación**: ranking independiente por temporada.
- **Estadísticas detalladas**: precisión, rachas, promedios.
- **Amigos e invitaciones**: compartidos entre temporadas (un solo grupo de amigos).
- **Sincronización automática** desde la API de football-data.org.
- **Diseño responsive** con Pico CSS.

## Requisitos

- Python 3.10+
- Django 6.0
- API Key de [football-data.org](https://www.football-data.org)

## Instalación

1. **Clonar el repositorio**
```bash
git clone <repo-url>
cd predigol
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

8. **Sincronizar partidos y calcular puntos de Champions League**
```bash
python manage.py sync_champions_matches
python manage.py calculate_champions_points
```

## Comandos de Gestión

| Comando | Descripción |
|---------|-------------|
| `python manage.py runserver` | Iniciar servidor de desarrollo |
| `python manage.py sync_champions_matches` | Sincronizar partidos UCL desde la API |
| `python manage.py calculate_champions_points` | Calcular puntos de partidos UCL finalizados |
| `python manage.py shell` | Abrir shell de Django |
| `python manage.py createsuperuser` | Crear administrador |

## Sistema de Puntos

### Champions League (temporada activa)
| Resultado | Puntos |
|-----------|--------|
| Resultado (1, X o 2) correcto | **3 pts** |
| Doble oportunidad (1X, X2 o 12) correcta | **1 pt** |
| Ninguna opción cubre el resultado | 0 pts |

Una sola elección por partido, tomada de un grupo de 6 opciones (1, X, 2, 1X, X2, 12).

### Mundial 2026 (solo lectura)
| Resultado | Puntos |
|-----------|--------|
| Marcador exacto | 3 pts |
| Resultado correcto | 2 pts |
| Cantidad de goles de un equipo | 1 pt |

## Arquitectura

```
predigol/
├── core/                    # Configuración del proyecto Django
│   ├── settings.py
│   └── urls.py              # incluye namespaces worldcup y champions
├── worldcup/                # Mundial 2026 (read-only)
│   ├── models.py            # Match, Prediction, PlayerStats, Friendship, InvitationCode
│   ├── views.py
│   ├── services.py
│   └── management/commands/
├── champions/               # UEFA Champions League (active)
│   ├── models.py            # Match, Prediction (1X2+DC), PlayerStats
│   ├── views.py
│   ├── urls.py
│   ├── services.py
│   ├── stats.py
│   ├── templatetags/
│   └── management/commands/
│       ├── sync_champions_matches.py
│       └── calculate_champions_points.py
├── templates/               # Plantillas HTML
│   ├── base.html            # champions base (root, active season)
│   ├── dashboard.html
│   ├── match_detail.html
│   ├── leaderboard.html
│   ├── profile.html
│   ├── user_predictions.html
│   ├── registration/        # signup/login compartidos
│   └── worldcup/            # plantillas Worldcup
│       ├── base.html
│       ├── dashboard.html
│       ├── match_detail.html
│       ├── leaderboard.html
│       ├── profile.html
│       ├── user_predictions.html
│       └── ...
├── db.sqlite3              # Base de datos
├── manage.py
├── run_hourly_tasks.py     # Cron job para Champions
└── .secret                 # Variables de entorno (no commitear)
```

## Rutas

### UEFA Champions League (raíz, temporada activa)
| Ruta | Descripción |
|------|-------------|
| `/` | Dashboard con partidos próximos y completados |
| `/match/<id>/` | Detalle de un partido con pronósticos |
| `/predictions/<username>/` | Pronósticos de un usuario |
| `/leaderboard/` | Tabla de clasificación |
| `/profile/` | Mi perfil y estadísticas |
| `/api/predict/` | Crear/actualizar pronóstico |
| `/friends/...` | Gestión de amigos e invitaciones |
| `/admin/` | Panel de administración |
| `/accounts/login/` | Iniciar sesión |
| `/accounts/signup/` | Registrarse |

### Mundial 2026 (`/worldcup/`, lectura)
| Ruta | Descripción |
|------|-------------|
| `/worldcup/` | Dashboard con partidos del Mundial |
| `/worldcup/match/<id>/` | Detalle de un partido del Mundial |
| `/worldcup/leaderboard/` | Clasificación Mundial |
| `/worldcup/profile/` | Perfil con stats Mundial |
| `/worldcup/api/predict/` | Crear/actualizar pronóstico Mundial |
| `/worldcup/friends/...` | Amigos e invitaciones (mismas tablas globales) |

## API Externa

Este proyecto utiliza la API de [football-data.org](https://api.football-data.org/v4).

- **Mundial 2026**: código `WC` (legacy, no se sincroniza más)
- **Champions League**: código `CL` (temporada activa)

## Tecnologías

- **Backend**: Django 6.0, Python 3.10+
- **Base de datos**: SQLite
- **Frontend**: HTML5, Pico CSS
- **API externa**: football-data.org
- **Gestión de configuración**: python-dotenv

## Licencia

MIT License
