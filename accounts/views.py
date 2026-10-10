import json

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse

from .models import Profile


def sign_in(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid json"}, status=400)

    username = body.get("username")
    password = body.get("password")

    if not username or not password:
        return JsonResponse(
            {"error": "Укажите логин и пароль"},
            status=400,
        )

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse(
            {"error": "Неверный логин или пароль"},
            status=401,
        )

    # Проверка архивации профиля
    profile = getattr(user, "profile", None)
    if profile and profile.archived:
        return JsonResponse(
            {"error": "Аккаунт архивирован"},
            status=403,
        )

    # Проверка is_active
    if not user.is_active:
        return JsonResponse(
            {"error": "Аккаунт отключён"},
            status=403,
        )

    login(request, user)

    # Привязка анонимных заказов по email
    from orders.models import Order
    Order.objects.filter(user=None, email=user.email).update(user=user)

    return JsonResponse({})




def sign_up(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid json"}, status=400)

    email = body.get("email", "")
    username = body.get("username")

    # Если username не передан — берём часть email до @
    if not username and email:
        base = email.split("@")[0]
        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1
    password = body.get("password")
    name = body.get("name", "") or body.get("fullName", "")
    phone = body.get("phone", "")

    if not username or not password:
        return JsonResponse({"error": "Укажите email и пароль"}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse(
            {"error": "Пользователь с указанным email существует, вы можете авторизоваться"},
            status=409,
        )

    if email and User.objects.filter(email=email).exists():
        return JsonResponse(
            {"error": "Пользователь с указанным email существует, вы можете авторизоваться"},
            status=409,
        )

    parts = name.split(" ", 1)
    first_name = parts[0] if parts else ""
    last_name = parts[1] if len(parts) > 1 else ""

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email or "",
        first_name=first_name,
        last_name=last_name,
    )
    profile, _ = Profile.objects.get_or_create(user=user)
    if phone:
        profile.phone = phone
        profile.save()

    login(request, user)

    # Привязка анонимных заказов по email
    from orders.models import Order
    Order.objects.filter(user=None, email=user.email).update(user=user)

    return JsonResponse({})


def sign_out(request):
    logout(request)
    return JsonResponse({})


def _validate_profile_data(body, user):
    """Проверка полей профиля. Возвращает (cleaned, errors)."""
    errors = {}
    cleaned = {}

    # fullName
    full_name = (body.get("fullName") or "").strip()
    if not full_name:
        errors["fullName"] = ["ФИО обязательно для заполнения"]
    elif len(full_name) < 2:
        errors["fullName"] = ["ФИО слишком короткое"]
    else:
        cleaned["fullName"] = full_name

    # email — обязателен, валидный, уникальный
    email = (body.get("email") or "").strip()
    if not email:
        errors["email"] = ["Email обязателен для заполнения"]
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors["email"] = ["Введите корректный email"]
        else:
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                errors["email"] = ["Этот email уже используется другим пользователем"]
            else:
                cleaned["email"] = email

    # phone — уникальный, если заполнен
    phone = (body.get("phone") or "").strip()
    if phone:
        digits = phone.replace("+", "").replace(" ", "")
        if not digits.isdigit() or not (10 <= len(digits) <= 15):
            errors["phone"] = ["Телефон должен содержать 10–15 цифр, допускается + в начале"]
        elif Profile.objects.filter(phone=phone).exclude(user=user).exists():
            errors["phone"] = ["Этот телефон уже используется другим пользователем"]
        else:
            cleaned["phone"] = phone

    return cleaned, errors


def profile_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "GET":
        return JsonResponse(_serialize_profile(request.user, profile))

    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "invalid json"}, status=400)

        cleaned, errors = _validate_profile_data(body, request.user)
        if errors:
            return JsonResponse(
                {"error": "validation failed", "errors": errors}, status=400
            )

        user = request.user
        # fullName → first_name + last_name
        if "fullName" in cleaned:
            parts = cleaned["fullName"].split(" ", 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ""
        if "email" in cleaned:
            user.email = cleaned["email"]
        user.save()

        if "phone" in cleaned:
            profile.phone = cleaned["phone"]
            profile.save()

        return JsonResponse(_serialize_profile(user, profile))

    return JsonResponse({"error": "Method not allowed"}, status=405)


def avatar_upload_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    avatar_file = request.FILES.get("avatar")
    if not avatar_file:
        return JsonResponse(
            {"error": "validation failed", "errors": {"avatar": ["Файл не передан"]}},
            status=400,
        )

    # Проверка размера ≤ 2 МБ
    if avatar_file.size > 2 * 1024 * 1024:
        return JsonResponse(
            {"error": "validation failed",
             "errors": {"avatar": ["Размер файла не должен превышать 2 МБ"]}},
            status=400,
        )

    # Проверка типа
    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if avatar_file.content_type not in allowed:
        return JsonResponse(
            {"error": "validation failed",
             "errors": {"avatar": ["Допустимы только изображения (jpg, png, webp, gif)"]}},
            status=400,
        )

    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.avatar = avatar_file
    profile.save()

    return JsonResponse({
        "src": profile.avatar.url,
        "alt": "User avatar",
    })


def change_password_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid json"}, status=400)

    current = body.get("currentPassword") or ""
    new = body.get("newPassword") or ""

    errors = {}
    if not current:
        errors["currentPassword"] = ["Укажите текущий пароль"]
    elif not request.user.check_password(current):
        errors["currentPassword"] = ["Неверный текущий пароль"]

    if not new:
        errors["newPassword"] = ["Укажите новый пароль"]
    elif len(new) < 8:
        errors["newPassword"] = ["Пароль должен быть не короче 8 символов"]

    if errors:
        return JsonResponse(
            {"error": "validation failed", "errors": errors}, status=400
        )

    request.user.set_password(new)
    request.user.save()
    update_session_auth_hash(request, request.user)

    return JsonResponse({})


def _serialize_profile(user, profile):
    if profile.avatar:
        avatar_src = profile.avatar.url
    else:
        avatar_src = "/static/frontend/assets/img/icons/user_icon.svg"
    return {
        "fullName": user.get_full_name() or user.username,
        "email": user.email,
        "phone": profile.phone,
        "avatar": {"src": avatar_src, "alt": "User avatar"},
    }
