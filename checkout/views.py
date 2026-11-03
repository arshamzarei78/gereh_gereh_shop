from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.models import Address
from accounts.forms import AddressForm
from cart.cart_module import Cart
from .models import Order,OrderItem
from django.db import transaction
@login_required
def checkout_view(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect("cart:cart_detail")

    user_addresses = request.user.addresses.select_related("province", "city").all()
    selected_address = (
        user_addresses.filter(is_default=True).first() or user_addresses.first()
    )

    if request.method == "POST":
        selected_address_id = request.POST.get("selected_address_id")

        if selected_address_id and selected_address_id != "new":
            addr_instance = get_object_or_404(
                Address, id=selected_address_id, user=request.user
            )
            form = AddressForm(request.POST, instance=addr_instance)
        else:
            # حالت ۲: کاربر می‌خواهد اطلاعات فرم به عنوان یک آدرس جدید به اکانتش اضافه شود
            form = AddressForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # ۱. ذخیره یا آپدیت آدرس
                    saved_address = form.save(commit=False)
                    saved_address.user = request.user

                    if not saved_address.pk:
                        saved_address.address_name = (
                            request.POST.get("address_name")
                            or f"آدرس {user_addresses.count() + 1}"
                        )
                        if not user_addresses.exists():
                            saved_address.is_default = True

                    saved_address.save()

                    # ۲. بررسی موجودی انبار قبل از ثبت سفارش
                    for item in cart:
                        variant = item["variant"]
                        if variant.stock < item["quantity"]:
                            raise ValueError(
                                f"موجودی محصول «{variant.product.name} ({variant.color})» کافی نیست. (موجودی فعلی: {variant.stock})"
                            )

                    # ۳. ایجاد سفارش اصلی (Order)
                    full_address_str = f"استان {saved_address.province.name}، شهر {saved_address.city.name}، {saved_address.address}"
                    
                    order = Order.objects.create(
                        user=request.user,
                        address=saved_address,
                        full_name=request.user.get_full_name(),
                        phone_number=request.user.phone_number,
                        address_text=full_address_str,
                        postal_code=saved_address.postal_code,
                        total_price=cart.get_total_price(), # متد محاسبه جمع کل در کلاس Cart شما
                        order_note=request.POST.get("order_note", ""),
                    )

                    # ۴. آماده‌سازی آیتم‌های سفارش برای ثبت یکجای بهینه (Bulk Create)
                    order_items = []
                    for item in cart:
                        variant = item["variant"]
                        size_str = f" - سایز: {variant.size}" if variant.size else ""
                        product_title = f"{variant.product.name} (رنگ: {variant.color}{size_str})"

                        order_items.append(
                            OrderItem(
                                order=order,
                                variant=variant,
                                product_name=product_title,
                                price=variant.final_price,  # قیمت نهایی با احتساب تخفیف
                                quantity=item["quantity"],
                            )
                        )

                    OrderItem.objects.bulk_create(order_items)

                    # ۵. خالی کردن سبد خرید (یا می‌توانید این مرحله را به بعد از تایید درگاه پرداخت موکول کنید)
                    cart.clear()

                # انتقال به صفحه درگاه پرداخت (یا صفحه موفقیت) به همراه آیدی سفارش
                return redirect("checkout:payment", order_id=order.id)

            except ValueError as e:
                # نمایش خطای کسری موجودی به کاربر در بالای فرم
                form.add_error(None, str(e))
    else:
        # در حالت باز شدن صفحه، اطلاعات آدرس پیش‌فرض را داخل فیلدها می‌نشانیم
        form = AddressForm(instance=selected_address)

    context = {
        "cart": cart,
        "form": form,
        "user_addresses": user_addresses,
        "selected_address": selected_address,
    }
    return render(request, "checkout/checkout.html", context)