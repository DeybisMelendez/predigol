from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('match/<int:match_id>/', views.match_detail, name='match_detail'),
    path('predictions/', views.user_predictions, name='user_predictions'),
    path('predictions/<str:username>/', views.user_predictions, name='user_predictions_by_username'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('profile/', views.profile, name='profile'),
    path('api/predict/', views.predict, name='predict'),
    path('friends/generate-invite/', views.generate_invite, name='generate_invite'),
    path('friends/invite/<str:code>/', views.accept_invite, name='accept_invite'),
    path('friends/remove/<str:username>/', views.remove_friend, name='remove_friend'),
]