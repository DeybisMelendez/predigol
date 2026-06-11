from django.contrib import admin
from django.utils.html import format_html
from .models import Match, Prediction, PlayerStats, Friendship, InvitationCode


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['home_team', 'away_team', 'datetime', 'stage', 'group', 'status_display', 'score_display']
    list_filter = ['status', 'stage', 'group']
    search_fields = ['home_team', 'away_team', 'venue']
    ordering = ['datetime']
    date_hierarchy = 'datetime'
    readonly_fields = ['match_id_externo']

    def status_display(self, obj):
        return obj.get_status_display()
    status_display.short_description = 'Estado'

    def score_display(self, obj):
        if obj.home_score is not None:
            return f"{obj.home_score} - {obj.away_score}"
        return "-"
    score_display.short_description = 'Resultado'


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['user', 'match', 'home_goals', 'away_goals', 'points', 'created_at']
    list_filter = ['points', 'created_at']
    search_fields = ['user__username', 'match__home_team', 'match__away_team']
    ordering = ['-created_at']
    raw_id_fields = ['user', 'match']
    readonly_fields = ['created_at']


@admin.register(PlayerStats)
class PlayerStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_points']
    search_fields = ['user__username']
    ordering = ['-total_points']
    raw_id_fields = ['user']


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ['user', 'friend', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'friend__username']
    ordering = ['-created_at']
    raw_id_fields = ['user', 'friend']


@admin.register(InvitationCode)
class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'creator', 'used_by', 'status_display', 'expires_at', 'created_at']
    list_filter = ['expires_at']
    search_fields = ['code', 'creator__username', 'used_by__username']
    ordering = ['-created_at']
    raw_id_fields = ['creator', 'used_by']
    readonly_fields = ['created_at']

    def status_display(self, obj):
        if obj.is_used:
            return "Usado"
        elif obj.is_expired:
            return "Expirado"
        return "Válido"
    status_display.short_description = 'Estado'