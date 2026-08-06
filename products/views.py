from django.shortcuts import render
from django.views.generic import DetailView
from .models import Product
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import ProductVariant
from .cart import Cart

class PtoductView(DetailView):
    model = Product


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    
    variant_id = request.POST.get("variant_id")
    quantity = int(request.POST.get("quantity", 1))

    if not variant_id:
        messages.error(request, "لطفاً یک تنوع (رنگ/سایز) انتخاب کنید.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    variant = get_object_or_404(ProductVariant, id=variant_id)

    # افزودن به سبد خرید
    cart.add(variant=variant, quantity=quantity)
    messages.success(request, f"{variant.product.name} با موفقیت به سبد خرید اضافه شد.")

    return redirect("home:home") #