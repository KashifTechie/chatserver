from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import AccountUser


@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def search_users(request):
    q = request.GET.get("q", "").strip()

    if not q:
        return Response([])

    users = AccountUser.objects.filter(
        Q(username__icontains=q) |
        Q(email__icontains=q)
    ).exclude(id=request.user.id)[:20]

    data = [
        {
            "id": u.id,
            "name": u.username,
            "email": u.email,
            "avatar": u.username[:2].upper(),
        }
        for u in users
    ]

    return Response(data)