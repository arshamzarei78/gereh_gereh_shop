from django.db.models import Avg, FloatField, Q
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from products.models import Product, ProductVariant
from .cart_module import Cart


def _is_ajax(request):
    """بررسی استاندارد درخواست‌های AJAX"""
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _build_cart_json_response(request, cart, message):
    """
    تابع کمکی (DRY) برای ساخت پاسخ یکپارچه JSON در تمام عملیات سبد خرید.
    این کار تضمین می‌کند فرانت‌اند همیشه دیتای کامل و یکسانی دریافت کند.
    """
    sidebar_html = render_to_string(
        "includes/sidebar-cart-content.html", {"cart": cart}, request=request
    )
    main_cart_html = render_to_string(
        "includes/cart-table-content.html", {"cart": cart}, request=request
    )
    return JsonResponse(
        {
            "status": "success",
            "message": message,
            "total_items": len(cart),
            "total_price": cart.get_total_price_display(),
            "sidebar_html": sidebar_html,
            "main_cart_html": main_cart_html,
        }
    )


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    variant_id = request.POST.get("variant_id")

    if not variant_id or not str(variant_id).isdigit():
        return JsonResponse(
            {"status": "error", "message": "لطفاً تنوع محصول (رنگ/سایز) را انتخاب کنید."},
            status=400,
        )

    try:
        quantity = int(request.POST.get("quantity", 1))
        if quantity < 1:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse(
            {"status": "error", "message": "تعداد وارد شده معتبر نیست."}, status=400
        )

    variant = get_object_or_404(
        ProductVariant.objects.select_related("product"),
        id=variant_id,
        product_id=product_id,
    )

    existing_qty = cart.cart.get(str(variant.id), {}).get("quantity", 0)
    if existing_qty + quantity > variant.stock:
        return JsonResponse(
            {
                "status": "error",
                "message": f"حداکثر موجودی قابل سفارش {variant.stock} عدد می‌باشد (شما هم‌اکنون {existing_qty} عدد در سبد دارید).",
            },
            status=400,
        )

    cart.add(variant=variant, quantity=quantity)

    if _is_ajax(request):
        return _build_cart_json_response(
            request, cart, f"{variant.product.name} به سبد خرید اضافه شد."
        )

    return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, variant_id):
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)

    cart.remove(variant)

    if _is_ajax(request):
        return _build_cart_json_response(
            request, cart, "محصول از سبد خرید حذف شد."
        )

    return redirect("cart:cart_detail")


@require_POST
def cart_update(request, variant_id):
    cart = Cart(request)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        return JsonResponse(
            {"status": "error", "message": "تعداد وارد شده معتبر نیست."}, status=400
        )

    variant = get_object_or_404(ProductVariant, id=variant_id)

    if quantity > variant.stock:
        return JsonResponse(
            {
                "status": "error",
                "message": f"حداکثر موجودی قابل سفارش {variant.stock} عدد می‌باشد.",
            },
            status=400,
        )

    cart.add(variant=variant, quantity=quantity, override_quantity=True)

    if _is_ajax(request):
        return _build_cart_json_response(
            request, cart, "تعداد محصول بروزرسانی شد."
        )

    return redirect("cart:cart_detail")


class CartDetail(TemplateView):
    template_name = "cart/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["popular_products"] = (
            Product.objects.annotate(
                calculated_rating=Coalesce(
                    Avg("comments__rating", filter=Q(comments__is_approved=True)),
                    5.0,
                    output_field=FloatField(),
                )
            )
            .prefetch_related("category", "variants", "images")
            .order_by("-calculated_rating", "-id")[:8]
        )
        return context