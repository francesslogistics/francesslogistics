from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Profile
from .serializers import (
    AccountUpdateSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    ProfileSerializer,
    RegisterSerializer,
    SelfProfileSerializer,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def ping(request):
    """Trivial, no-auth endpoint the front-end pings on load to check whether
    the backend is reachable at all, before it tries to actually sign in."""
    return Response({"status": "ok"})


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    profile, _ = Profile.objects.get_or_create(user=user)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        "token": token.key,
        "name": profile.display_name,
        "position": profile.position,
        "photo": profile.photo,
        "rank": profile.rank,
        "username": user.username,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    # Invalidate the token so it can't be reused, then clear any session too.
    Token.objects.filter(user=request.user).delete()
    django_logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_view(request):
    """Creates a new login. CEO-only — this used to be AllowAny, which meant
    anyone (even logged out) could hit this endpoint directly and create an
    account. The front-end already hides the button from non-CEOs, but that's
    just UI; this is the actual enforcement."""
    my_profile, _ = Profile.objects.get_or_create(user=request.user)
    if my_profile.position != Profile.Position.CEO:
        return Response(
            {"detail": "Only the CEO account can create new accounts."},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "username": user.username}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "PATCH":
        # Deliberately uses SelfProfileSerializer, not ProfileSerializer —
        # position is read-only here. A user can never promote/demote
        # themselves; that only happens via accounts_detail_view below,
        # and only by someone who outranks them.
        serializer = SelfProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    return Response(SelfProfileSerializer(profile).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    request.user.set_password(serializer.validated_data["new_password"])
    request.user.save()
    # Rotate the auth token so the old one (and any other open session) can't
    # keep using the now-changed password's session; front-end re-logs-in.
    Token.objects.filter(user=request.user).delete()
    token = Token.objects.create(user=request.user)
    return Response({"token": token.key})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def accounts_list_view(request):
    """Powers the Accounts page — every user's profile, plus whether the
    requesting user is allowed to edit each one (strictly-lower rank only)."""
    my_profile, _ = Profile.objects.get_or_create(user=request.user)
    accounts = []
    for profile in Profile.objects.select_related("user").order_by("user__username"):
        data = ProfileSerializer(profile).data
        data["id"] = profile.user_id
        data["can_edit"] = my_profile.rank > profile.rank
        accounts.append(data)
    return Response({"accounts": accounts, "my_rank": my_profile.rank, "position_choices": Profile.Position.values})


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def accounts_detail_view(request, user_id):
    """Change — or permanently delete — another user's account. Only allowed
    if the requester outranks the target's CURRENT position (same rule for
    both actions), and a position change may only assign something that
    still ranks below the requester's own (no promoting someone above or
    to your own level)."""
    my_profile, _ = Profile.objects.get_or_create(user=request.user)
    target_profile = Profile.objects.select_related("user").filter(user_id=user_id).first()
    if not target_profile:
        return Response({"detail": "Account not found."}, status=status.HTTP_404_NOT_FOUND)
    if my_profile.rank <= target_profile.rank:
        return Response(
            {"detail": "You don't have permission to modify this account."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == "DELETE":
        # Deletes the underlying Django User row. Profile cascades (OneToOne,
        # on_delete=CASCADE) and so does the auth Token, so this is a real,
        # permanent removal from the database — not a soft/trash delete.
        target_profile.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = AccountUpdateSerializer(target_profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    new_position = serializer.validated_data.get("position", target_profile.position)
    if new_position and Profile.RANK.get(new_position, 0) >= my_profile.rank:
        return Response(
            {"detail": "You can't assign a position at or above your own rank."},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer.save()
    return Response(ProfileSerializer(target_profile).data)
