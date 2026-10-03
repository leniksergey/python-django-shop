import json
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import Profile



def sign_in(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    body = json.loads(request.body)
    user = authenticate(
        request, username=body.get("username"), password=body.get("password")
    )
    if user is None:
        return JsonResponse({"error": "invalid credentials"}, status=500)
    login(request, user)
    return JsonResponse({})


def sign_up(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    body = json.loads(request.body)
    username, password = body.get("username"), body.get("password")
    if not username or not password or User.objects.filter(username=username).exists():
        return JsonResponse({"error": "invalid data"}, status=500)

    user = User.objects.create_user(
        username=username, password=password, first_name=body.get("name", "")
    )
    Profile.objects.create(user=user)
    login(request, user)
    return JsonResponse({})


def sign_out(request):
    logout(request)
    return JsonResponse({})



def profile_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "GET":
        avatar_src = profile.avatar.url if profile.avatar else "/media/avatars/default.png"

        data = {
            "fullName": request.user.get_full_name() or request.user.username,
            "email": request.user.email,
            "phone": profile.phone,
            "avatar": {
                "src": avatar_src,
                "alt": "User avatar",
            },
        }
        return JsonResponse(data)

    if request.method == "POST":
        body = json.loads(request.body)
        user = request.user

        full_name = body.get("fullName", "").strip()
        if full_name:
            name_parts = full_name.split(" ", 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ""

        user.email = body.get("email", user.email)
        user.save()

        profile.phone = body.get("phone", profile.phone)
        profile.save()

        avatar_src = profile.avatar.url if profile.avatar else "/media/avatars/default.png"

        return JsonResponse({
            "fullName": f"{user.first_name} {user.last_name}".strip() or user.username,
            "email": user.email,
            "phone": profile.phone,
            "avatar": {
                "src": avatar_src,
                "alt": "User avatar",
            },
        })

    return JsonResponse({"error": "Method not allowed"}, status=405)


def avatar_upload_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method == "POST":
        avatar_file = request.FILES.get("avatar")
        if not avatar_file:
            return JsonResponse({"error": "No file provided"}, status=400)

        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.avatar = avatar_file
        profile.save()

        return JsonResponse({
            "src": profile.avatar.url,
            "alt": "User avatar"
        })

    return JsonResponse({"error": "Method not allowed"}, status=405)


def change_password_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method == "POST":
        body = json.loads(request.body)
        current_password = body.get("currentPassword")
        new_password = body.get("newPassword")

        if not request.user.check_password(current_password):
            return JsonResponse({"error": "Invalid current password"}, status=400)

        request.user.set_password(new_password)
        request.user.save()

        update_session_auth_hash(request, request.user)

        return JsonResponse({})

    return JsonResponse({"error": "Method not allowed"}, status=405)
