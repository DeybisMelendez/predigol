# Mundial

Este es un minijuego que permite jugar a adivinar los resultados de los partidos de la copa del mundo.

Si aciertas ganas puntos y hay un tablero de clasificación general para ver quien tiene mas puntos.

Utilizamos la api de https://www.football-data.org

Script de ejemplo:

import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=".secret")
FOOTBALL_DATA_KEY = os.environ.get("DJANGO_DEBUG", "")

class FootballDataAPI:
    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self, api_key):
        self.headers = {
            "X-Auth-Token": api_key
        }

    def _get(self, endpoint, params=None):
        url = f"{self.BASE_URL}/{endpoint}"

        response = requests.get(
            url,
            headers=self.headers,
            params=params
        )

        response.raise_for_status()

        return response.json()

    def upcoming_matches(self, competition="WC", limit=10):
        """
        Próximos partidos.
        WC = World Cup
        """

        data = self._get(
            f"competitions/{competition}/matches",
            {
                "status": "SCHEDULED"
            }
        )

        return data["matches"][:limit]

    def finished_matches(self, competition="WC", limit=10):
        """
        Últimos resultados.
        """

        data = self._get(
            f"competitions/{competition}/matches",
            {
                "status": "FINISHED"
            }
        )

        return data["matches"][-limit:]