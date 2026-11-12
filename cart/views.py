from django.shortcuts import get_object_or_404 , redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from products.models import ProductVariant,Product
from .cart_module import Cart
from django.views.generic import TemplateView
from django.db.models import Avg, Q, FloatField
from django.db.models.functions import Coalesce

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    
    variant_id = request.POST.get("variant_id")
    quantity = int(request.POST.get("quantity", 1))

    variant = get_object_or_404(ProductVariant, id=variant_id)

    if quantity > variant.stock:
        return JsonResponse({
            'status': 'error',
            'message': f'حداکثر موجودی قابل سفارش {variant.stock} عدد می‌باشد.'
        }, status=400)

    if not variant_id:
        return JsonResponse({"status": "error", "message": "لطفاً تنوع محصول را انتخاب کنید."}, status=400)

    # افزودن محصول به سبد
    cart.add(variant=variant, quantity=quantity)

    # اگر درخواست Ajax بود، HTML جدید سایدبار را رندر و ارسال می‌کنیم
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # رندر کردن جزئیات جدید سایدبار در قالب یک HTML partial
        sidebar_html = render_to_string('includes/sidebar-cart.html', {'cart': cart}, request=request)
        
        return JsonResponse({
            "status": "success",
            "message": f"{variant.product.name} به سبد خرید اضافه شد.",
            "total_items": len(cart),
            "total_price": f"{cart.get_total_price():,} تومان",
            "sidebar_html": sidebar_html
        })

    # پشتیبانی از فرم معمولی بدون Ajax
    return redirect("home:home")

@require_POST
def cart_remove(request, variant_id):
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    
    # حذف از سبد خرید
    cart.remove(variant)
    
    # اگر درخواست Ajax بود (چه از سایدبار چه از صفحه اصلی)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        sidebar_html = render_to_string('includes/sidebar-cart-content.html', {'cart': cart}, request=request)
        
        return JsonResponse({
            "status": "success",
            "message": "محصول از سبد خرید حذف شد.",
            "total_items": len(cart),
            "sidebar_html": sidebar_html
        })
        
    # در صورت عدم استفاده از ای‌جکس
    return redirect("cart:cart_detail")

@require_POST
def cart_update(request, variant_id):
    cart = Cart(request)
    
    # دریافت تعداد جدید از درخواست
    quantity = int(request.POST.get("quantity", 1))

    # پیدا کردن تنوع محصول با آیدی دریافت شده از url
    variant = get_object_or_404(ProductVariant, id=variant_id)

    # بررسی سقف موجودی
    if quantity > variant.stock:
        return JsonResponse({
            'status': 'error',
            'message': f'حداکثر موجودی قابل سفارش {variant.stock} عدد می‌باشد.'
        }, status=400)

    # آپدیت سبد خرید (جایگزینی تعداد جدید)
    cart.add(variant=variant, quantity=quantity, override_quantity=True)

    # اگر درخواست Ajax بود
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # دقت کنید که آدرس فایل کانتنت را دادیم
        sidebar_html = render_to_string('includes/sidebar-cart-content.html', {'cart': cart}, request=request)
        main_cart_html = render_to_string('includes/cart-table-content.html', {'cart': cart}, request=request)
        return JsonResponse({
            "status": "success",
            "message": "تعداد محصول بروزرسانی شد.",
            "total_items": len(cart),
            "total_price": cart.get_total_price_display(), # یا فیلتر intcomma
            "sidebar_html": sidebar_html,
            "main_cart_html": main_cart_html
        })

class CartDetail(TemplateView):
    template_name = "cart/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # واکشی ۸ محصول با بالاترین میانگین امتیاز (محصولات بدون نظر، امتیاز پیش‌فرض 5.0 می‌گیرند)
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