import json

from django.core.paginator import Paginator
from django.db.models import Avg, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import Category, Product, Review

PLACEHOLDER = "/static/frontend/assets/img/content/home/card.jpg"
CATEGORY_PLACEHOLDER = "/static/frontend/assets/img/icons/allDep.svg"
SORT_FIELDS = {"price": "price", "date": "created_at"}


def catalog(request):
    params = request.GET
    products = Product.objects.all()

    category_id = params.get("category")
    if category_id:
        products = products.filter(
            Q(category_id=category_id) | Q(category__parent_id=category_id)
        )

    name = params.get("filter[name]")
    if name:
        products = products.filter(title__icontains=name)

    products = products.filter(
        price__gte=params.get("filter[minPrice]", 0),
        price__lte=params.get("filter[maxPrice]", 1000000),
    )

    if params.get("filter[freeDelivery]") == "true":
        products = products.filter(free_delivery=True)

    if params.get("filter[available]") == "true":
        products = products.filter(count__gt=0)

    field = SORT_FIELDS.get(params.get("sort"), "created_at")
    if params.get("sortType") == "dec":
        field = "-" + field

    paginator = Paginator(products.order_by(field), int(params.get("limit", 20)))
    page = paginator.get_page(params.get("currentPage", 1))

    return JsonResponse({
        "items": [product_short(product) for product in page],
        "currentPage": page.number,
        "lastPage": paginator.num_pages,
    })


# noinspection PyUnusedLocal
def tags(request):
    return JsonResponse([], safe=False)


def serialize_category(category: Category):
    return {
        "id": category.pk,
        "title": category.title,
        "image": {
            "src": category.image.url if category.image else CATEGORY_PLACEHOLDER,
            "alt": category.title,
        },
    }


# noinspection PyUnusedLocal
def categories(request):
    category_list = Category.objects.filter(parent=None).prefetch_related('subcategories')
    data = []
    for category in category_list:
        item = serialize_category(category)
        item["subcategories"] = [
            serialize_category(subcategory)
            for subcategory in category.subcategories.all()
        ]
        data.append(item)
    return JsonResponse(data, safe=False)


def product_images(product: Product):
    images = [
        {"src": image.image.url, "alt": product.title}
        for image in product.images.all()
    ]
    return images or [{"src": PLACEHOLDER, "alt": product.title}]


def avg_rating(product: Product):
    """Средняя оценка по неархивированным отзывам товара."""
    result = product.reviews.filter(archived=False).aggregate(avg=Avg("rate"))
    return round(result["avg"] or 0, 1)


def serialize_review(review):
    profile = getattr(review.user, "profile", None)
    avatar_url = "/static/frontend/assets/img/icons/user_icon.svg"
    if profile and profile.avatar:
        avatar_url = profile.avatar.url
    return {
        "id": review.pk,
        "author": review.user.get_full_name() or review.user.username,
        "date": review.created_at.strftime("%Y-%m-%d"),
        "rate": review.rate,
        "text": review.text,
        "avatar": avatar_url,
    }


def product_short(product: Product):
    return {
        "id": product.pk,
        "category": product.category_id,
        "price": float(product.price),
        "salePrice": float(product.sale_price) if product.sale_price else None,  # ← добавить
        "count": product.count,
        "date": product.created_at.isoformat(),
        "title": product.title,
        "description": product.description,
        "freeDelivery": product.free_delivery,
        "images": product_images(product),
        "tags": [],
        "reviews": product.reviews.filter(archived=False).count(),
        "rating": avg_rating(product),
    }


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        # Добавление отзыва — только для авторизованных
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        try:
            body = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "invalid json"}, status=400)

        text = (body.get("text") or "").strip()
        try:
            rate = int(body.get("rate") or 5)
        except (TypeError, ValueError):
            rate = 5

        errors = {}
        if not text:
            errors["text"] = ["Текст отзыва обязателен"]
        if not (1 <= rate <= 5):
            errors["rate"] = ["Оценка должна быть от 1 до 5"]

        if errors:
            return JsonResponse(
                {"error": "validation failed", "errors": errors}, status=400
            )

        review = Review.objects.create(
            product=product,
            user=request.user,
            text=text,
            rate=rate,
        )
        return JsonResponse(serialize_review(review), status=201)

    # GET — карточка товара с отзывами
    data = product_short(product)
    reviews = (
        product.reviews
        .filter(archived=False)
        .select_related("user")
        .order_by("created_at")[:3]
    )
    data.update({
        "fullDescription": product.description,
        "tags": [],
        "reviews": [serialize_review(r) for r in reviews],
        "reviewsLastPage": max(1, (product.reviews.filter(archived=False).count() + 2) // 3),
        "totalReviews": product.reviews.filter(archived=False).count(),
        "specifications": [],
    })
    return JsonResponse(data)


def product_sale(product: Product):
    return {
        "id": product.pk,
        "title": product.title,
        "price": float(product.price or 0),
        "salePrice": float(product.sale_price or 0),
        "images": product_images(product),
    }


def product_reviews(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = (
        product.reviews
        .filter(archived=False)
        .select_related("user")
        .order_by("created_at")
    )
    page_num = int(request.GET.get("page", 1))
    if page_num <= 1:
        items = [serialize_review(r) for r in reviews[:3]]
    else:
        items = [serialize_review(r) for r in reviews]
    return JsonResponse({
        "items": items,
        "currentPage": page_num,
        "lastPage": 1,
    })


def basket_data(request):
    cart = request.session.get("basket", {})
    products = Product.objects.filter(id__in=[int(key) for key in cart])
    items = []
    for product in products:
        item = product_short(product)
        item["count"] = cart[str(product.pk)]
        items.append(item)
    return items


def basket(request):
    if request.method in ("POST", "DELETE"):
        body = json.loads(request.body)
        if "id" not in body:
            return JsonResponse({"error": "id is required"}, status=400)
        product_key, count = str(body["id"]), int(body["count"])
        cart = request.session.get("basket", {})
        if request.method == "POST":
            cart[product_key] = cart.get(product_key, 0) + count
        else:
            cart[product_key] = cart.get(product_key, 0) - count
            if cart[product_key] <= 0:
                del cart[product_key]
        request.session["basket"] = cart
    return JsonResponse(basket_data(request), safe=False)


# noinspection PyUnusedLocal
def popular(request):
    products = Product.objects.order_by("-sort_index", "-sold")[:8]
    return JsonResponse([product_short(product) for product in products], safe=False)


# noinspection PyUnusedLocal
def limited(request):
    products = Product.objects.filter(limited=True)[:16]
    return JsonResponse([product_short(product) for product in products], safe=False)


# noinspection PyUnusedLocal
def banners(request):
    products = Product.objects.order_by("-created_at")[:3]
    return JsonResponse([product_short(product) for product in products], safe=False)


def sales(request):
    """API раздела Sales: товары со скидкой с пагинацией."""
    products = Product.objects.filter(sale_price__isnull=False)
    paginator = Paginator(products.order_by("-created_at"), 12)
    page = paginator.get_page(request.GET.get("currentPage", 1))
    return JsonResponse({
        "items": [product_sale(product) for product in page],
        "currentPage": page.number,
        "lastPage": paginator.num_pages,
    })
