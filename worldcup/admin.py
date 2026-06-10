from django.contrib import admin
from .models import Match, Prediction


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['home_team', 'away_team', 'datetime', 'stage', 'group', 'status', 'home_score', 'away_score']
    list_filter = ['status', 'stage', 'group']
    search_fields = ['home_team', 'away_team']
    ordering = ['datetime']


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['user', 'match', 'home_goals', 'away_goals', 'points', 'created_at']
    list_filter = ['points']
    search_fields = ['user__username', 'match__home_team', 'match__away_team']
    ordering = ['-created_at']