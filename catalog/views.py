import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import Category, Product

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


def product_short(product: Product):
    return {
        "id": product.pk,
        "category": product.category_id,
        "price": float(product.price),
        "count": product.count,
        "date": product.created_at.isoformat(),
        "title": product.title,
        "description": product.description,
        "freeDelivery": product.free_delivery,
        "images": product_images(product),
        "tags": [],
        "reviews": 0,
        "rating": 0,
    }


# noinspection PyUnusedLocal
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    data = product_short(product)
    data.update({
        "fullDescription": product.description,
        "tags": [],
        "reviews": [],
        "specifications": [],
    })
    return JsonResponse(data)


def product_images(product: Product):
    images = [
        {"src": image.image.url, "alt": product.title}
        for image in product.images.all()
    ]
    return images or [{"src": PLACEHOLDER, "alt": product.title}]


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
