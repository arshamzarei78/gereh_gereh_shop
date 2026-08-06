from django.shortcuts import get_object_or_404 , redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from products.models import ProductVariant
from .cart_module import Cart

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    
    variant_id = request.POST.get("variant_id")
    quantity = int(request.POST.get("quantity", 1))

    if quantity > variant.stock:
        return JsonResponse({
            'status': 'error',
            'message': f'حداکثر موجودی قابل سفارش {variant.stock} عدد می‌باشد.'
        }, status=400)

    if not variant_id:
        return JsonResponse({"status": "error", "message": "لطفاً تنوع محصول را انتخاب کنید."}, status=400)

    variant = get_object_or_404(ProductVariant, id=variant_id)

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

@require_POST  # یا بدون آن برای لینک‌های مستقیم
def cart_remove(request, variant_id):
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    cart.remove(variant)
    return redirect("home:home")


def cart_detail(request):
    pass