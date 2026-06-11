from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.db.models import Sum
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, date
from collections import defaultdict
from .models import Match, Prediction, PlayerStats

MATCH_START_BUFFER = timedelta(minutes=5)

DAY_NAMES_ES = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}

MONTH_NAMES_ES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}


def get_date_label(match_date, today):
    delta = (match_date - today).days
    if delta == 0:
        return "Hoy"
    elif delta == 1:
        return "Mañana"
    elif delta == 2:
        return "Pasado Mañana"
    else:
        day_name = DAY_NAMES_ES[match_date.weekday()]
        month_name = MONTH_NAMES_ES[match_date.month]
        return f"{day_name} {match_date.day} {month_name}"


def dashboard(request):
    today = timezone.localdate()
    upcoming_matches = Match.objects.filter(status__in=['SCHEDULED', 'TIMED']).order_by('datetime')
    finished_matches = Match.objects.filter(status='FINISHED').order_by('-datetime')

    user_predictions = {}
    if request.user.is_authenticated:
        predictions = Prediction.objects.filter(user=request.user).select_related('match')
        user_predictions = {p.match_id: p for p in predictions}

    for match in upcoming_matches:
        match.user_prediction = user_predictions.get(match.id)

    upcoming_by_date = defaultdict(list)
    for match in upcoming_matches:
        match_date = timezone.localtime(match.datetime).date()
        upcoming_by_date[match_date].append(match)

    sorted_dates = sorted(upcoming_by_date.keys())
    upcoming_matches_by_date = [
        {
            'date': d,
            'label': get_date_label(d, today),
            'matches': upcoming_by_date[d]
        }
        for d in sorted_dates
    ]

    context = {
        'upcoming_matches_by_date': upcoming_matches_by_date,
        'finished_matches': finished_matches,
    }
    return render(request, 'dashboard.html', context)


def match_detail(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    predictions = Prediction.objects.filter(match=match).select_related('user').order_by('-points', 'created_at')
    user_prediction = None
    if request.user.is_authenticated:
        user_prediction = Prediction.objects.filter(match=match, user=request.user).first()
    context = {
        'match': match,
        'predictions': predictions,
        'user_prediction': user_prediction,
    }
    return render(request, 'match_detail.html', context)


def user_predictions(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
        predictions = Prediction.objects.filter(user=user).select_related('match')
        is_own = request.user.is_authenticated and request.user == user
    elif request.user.is_authenticated:
        return redirect('user_predictions_by_username', username=request.user.username)
    else:
        return redirect('login')
    context = {
        'profile_user': user,
        'predictions': predictions,
        'is_own': is_own,
    }
    return render(request, 'user_predictions.html', context)


@login_required
def my_predictions(request):
    return redirect('user_predictions_by_username', username=request.user.username)


@login_required
def profile(request):
    all_users = (
        User.objects
        .filter(prediction__isnull=False)
        .annotate(total_points=Sum('prediction__points'))
        .order_by('-total_points')
    )
    total_users = all_users.count()
    position = None
    for i, user in enumerate(all_users, 1):
        if user.id == request.user.id:
            position = i
            break

    context = {
        'position': position,
        'total_users': total_users,
    }
    return render(request, 'profile.html', context)


def leaderboard(request):
    leaderboard_data = (
        User.objects
        .filter(prediction__isnull=False)
        .annotate(total_points=Sum('prediction__points'))
        .order_by('-total_points')[:20]
    )

    user_stats = None
    user_position = None
    if request.user.is_authenticated:
        try:
            user_stats = PlayerStats.objects.get(user=request.user)
            user_position = list(
                User.objects
                .filter(prediction__isnull=False)
                .annotate(total_points=Sum('prediction__points'))
                .order_by('-total_points')
                .values_list('id', flat=True)
            ).index(request.user.id) + 1
        except PlayerStats.DoesNotExist:
            pass

    context = {
        'leaderboard': leaderboard_data,
        'user_stats': user_stats,
        'user_position': user_position,
    }
    return render(request, 'leaderboard.html', context)


@login_required
def predict(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        match_id = data.get('match_id')
        home_goals = data.get('home_goals')
        away_goals = data.get('away_goals')

        match = get_object_or_404(Match, id=match_id)

        if match.status not in ['SCHEDULED', 'TIMED']:
            return JsonResponse({'error': 'Match already started or finished'}, status=400)

        now = timezone.now()
        match_start_with_buffer = match.datetime - MATCH_START_BUFFER
        if now >= match_start_with_buffer:
            return JsonResponse({'error': 'Match starting soon or already in progress'}, status=400)

        prediction, created = Prediction.objects.update_or_create(
            user=request.user,
            match=match,
            defaults={'home_goals': home_goals, 'away_goals': away_goals}
        )

        return JsonResponse({'success': True, 'created': created})
    return JsonResponse({'error': 'Invalid method'}, status=405)


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'registration/signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'registration/signup.html')

        user = User.objects.create_user(username=username, password=password1)
        login(request, user)
        return redirect('dashboard')

    return render(request, 'registration/signup.html')