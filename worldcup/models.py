from django.db import models
from django.contrib.auth.models import User


class Match(models.Model):
    STAGE_CHOICES = [
        ('PRELIMINARY_ROUND', 'Ronda Preliminar'),
        ('GROUP_STAGE', 'Fase de Grupos'),
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
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES)
    group = models.CharField(max_length=2, blank=True, null=True)
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    home_goals = models.IntegerField()
    away_goals = models.IntegerField()
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'match']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.match.home_team} {self.home_goals}-{self.away_goals} {self.match.away_team}"

    def _get_result(self):
        if self.home_goals > self.away_goals:
            return 'H'
        elif self.home_goals < self.away_goals:
            return 'A'
        return 'D'

    def calculate_points(self):
        if self.match.is_finished and self.match.home_score is not None:
            pred_result = self._get_result()
            match_result = self.match._get_result()

            if self.home_goals == self.match.home_score and self.away_goals == self.match.away_score:
                self.points = 3
            elif pred_result == match_result:
                self.points = 2
            elif self.home_goals == self.match.home_score or self.away_goals == self.match.away_score:
                self.points = 1
            else:
                self.points = 0
            self.save()
        return self.points


class PlayerStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stats')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    total_predictions = models.IntegerField(default=0)
    exact_count = models.IntegerField(default=0)
    winner_count = models.IntegerField(default=0)
    goals_count = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0)