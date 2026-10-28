from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import User

@login_required
def profile(request):
    """Display basic profile information for the logged‑in user."""
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'accounts/profile.html', context)
