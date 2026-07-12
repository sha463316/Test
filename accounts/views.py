import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer
from django.contrib.auth import authenticate

logger = logging.getLogger("accounts")


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    correlation_id = getattr(request, "correlation_id", None)
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    refresh = RefreshToken.for_user(user)
    logger.info("user.registered", extra={
        "user_id": str(user.id),
        "username": user.username,
        "correlation_id": correlation_id,
    })
    return Response(
        {"access": str(refresh.access_token), "refresh": str(refresh)},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    correlation_id = getattr(request, "correlation_id", None)
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(
        username=serializer.validated_data["username"],
        password=serializer.validated_data["password"],
    )
    if not user:
        logger.warning("user.login_failed", extra={
            "username": serializer.validated_data["username"],
            "correlation_id": correlation_id,
        })
        return Response(
            {"error": "invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )
    refresh = RefreshToken.for_user(user)
    logger.info("user.logged_in", extra={
        "user_id": str(user.id),
        "username": user.username,
        "correlation_id": correlation_id,
    })
    return Response({"access": str(refresh.access_token), "refresh": str(refresh)})
