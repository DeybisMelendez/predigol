from django.db import models
from django.contrib.auth.models import User


class Match(models.Model):
    STAGE_CHOICES = [
        ('QUALIFYING', 'Ronda Clasificatoria'),
        ('QUALIFICATION_ROUND_1', 'Ronda Clasificatoria 1'),
        ('QUALIFICATION_ROUND_2', 'Ronda Clasificatoria 2'),
        ('QUALIFICATION_ROUND_3', 'Ronda Clasificatoria 3'),
        ('PLAYOFF_ROUND', 'Playoff'),
        ('GROUP_STAGE', 'Fase de Grupos'),
        ('LEAGUE_STAGE', 'Fase de Liga'),
        ('LEAGUE_PHASE', 'Fase de Liga'),
        ('ROUND_OF_16', 'Octavos de Final'),
        ('QUARTER_FINALS', 'Cuartos de Final'),
        ('SEMI_FINALS', 'Semifinales'),
        ('THIRD_PLACE', 'Tercer Lugar'),
        ('FINAL', 'Final'),
    ]

    STATUS_CHOICES = [
        ('SCHEDULED', 'Programado'),
        ('TIMED', 'Programado'),
        ('IN_PLAY', 'En Juego'),
        ('PAUSED', 'Pausado'),
        ('FINISHED', 'Finalizado'),
        ('POSTPONED', 'Pospuesto'),
        ('SUSPENDED', 'Suspendido'),
        ('CANCELLED', 'Cancelado'),
    ]

    match_id_externo = models.IntegerField(unique=True)
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    home_team_crest = models.URLField(max_length=300, blank=True, null=True)
    away_team_crest = models.URLField(max_length=300, blank=True, null=True)
    datetime = models.DateTimeField()
    stage = models.CharField(max_length=30, choices=STAGE_CHOICES)
    group = models.CharField(max_length=10, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    home_score = models.IntegerField(blank=True, null=True)
    away_score = models.IntegerField(blank=True, null=True)
    home_lineup = models.JSONField(blank=True, null=True)
    away_lineup = models.JSONField(blank=True, null=True)
    goals = models.JSONField(blank=True, null=True)
    bookings = models.JSONField(blank=True, null=True)
    substitutions = models.JSONField(blank=True, null=True)
    venue = models.CharField(max_length=200, blank=True, null=True)
    attendance = models.IntegerField(blank=True, null=True)
    injury_time = models.IntegerField(blank=True, null=True)
    home_coach = models.CharField(max_length=100, blank=True, null=True)
    away_coach = models.CharField(max_length=100, blank=True, null=True)
    home_formation = models.CharField(max_length=20, blank=True, null=True)
    away_formation = models.CharField(max_length=20, blank=True, null=True)
    home_bench = models.JSONField(blank=True, null=True)
    away_bench = models.JSONField(blank=True, null=True)
    referees = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['datetime']

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} ({self.datetime.strftime('%Y-%m-%d %H:%M')})"

    @property
    def is_finished(self):
        return self.status == 'FINISHED'

    def _get_result(self):
        if self.home_score is None:
            return None
        if self.home_score > self.away_score:
            return 'H'
        elif self.home_score < self.away_score:
            return 'A'
        return 'D'


class Prediction(models.Model):
    PICK_CHOICES = [
        ('HOME',          '1'),
        ('DRAW',          'X'),
        ('AWAY',          '2'),
        ('HOME_OR_DRAW',  '1X'),
        ('DRAW_OR_AWAY',  'X2'),
        ('HOME_OR_AWAY',  '12'),
    ]
    PICK_1X2 = {'HOME', 'DRAW', 'AWAY'}
    PICK_DOUBLE_CHANCE = {'HOME_OR_DRAW', 'DRAW_OR_AWAY', 'HOME_OR_AWAY'}

    PICK_GROUPS = [
        ('1X2', 'Resultado', [
            ('HOME', '1'),
            ('DRAW', 'X'),
            ('AWAY', '2'),
        ]),
        ('DOUBLE_CHANCE', 'Doble oportunidad', [
            ('HOME_OR_DRAW', '1X'),
            ('DRAW_OR_AWAY', 'X2'),
            ('HOME_OR_AWAY', '12'),
        ]),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='champions_predictions')
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    pick = models.CharField(max_length=16, choices=PICK_CHOICES)
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'match']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.match.home_team} vs {self.match.away_team} -> {self.get_pick_display()}"

    @property
    def pick_label(self):
        return dict(self.PICK_CHOICES).get(self.pick, self.pick)

    @property
    def is_double_chance(self):
        return self.pick in self.PICK_DOUBLE_CHANCE

    @property
    def is_1x2(self):
        return self.pick in self.PICK_1X2

    def _covers(self, result_char):
        result_to_pick = {'H': 'HOME', 'D': 'DRAW', 'A': 'AWAY'}
        pick_value = result_to_pick.get(result_char)
        table = {
            'HOME':         {'HOME'},
            'DRAW':         {'DRAW'},
            'AWAY':         {'AWAY'},
            'HOME_OR_DRAW': {'HOME', 'DRAW'},
            'DRAW_OR_AWAY': {'DRAW', 'AWAY'},
            'HOME_OR_AWAY': {'HOME', 'AWAY'},
        }
        return pick_value in table[self.pick]

    def calculate_points(self):
        if not self.match.is_finished or self.match.home_score is None:
            return self.points
        result = self.match._get_result()
        result_to_pick = {'H': 'HOME', 'D': 'DRAW', 'A': 'AWAY'}
        if self.pick in self.PICK_1X2:
            self.points = 3 if self.pick == result_to_pick.get(result) else 0
        else:
            self.points = 1 if self._covers(result) else 0
        self.save()
        return self.points


class PlayerStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='champions_stats')
    total_points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}: {self.total_points} pts"
