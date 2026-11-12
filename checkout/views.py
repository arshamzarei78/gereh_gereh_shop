import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from accounts.forms import AddressForm
from accounts.models import Address
from cart.cart_module import Cart
from products.models import ProductVariant
from .models import Order, OrderItem,ShippingSetting

# تنظیم آدرس‌های وب‌سرویس زرین‌پال بر اساس حالت Sandbox یا واقعی
if getattr(settings, "SANDBOX", True):
    ZP_API_REQUEST = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
    ZP_API_VERIFY = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
    ZP_API_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay/"
else:
    ZP_API_REQUEST = "https://payment.zarinpal.com/pg/v4/payment/request.json"
    ZP_API_VERIFY = "https://payment.zarinpal.com/pg/v4/payment/verify.json"
    ZP_API_STARTPAY = "https://payment.zarinpal.com/pg/StartPay/"



def checkout_view(request):
    if not request.user.is_authenticated:
        return redirect("accounts:verify_otp")
    cart = Cart(request)
    if len(cart) == 0:
        return redirect("cart:cart_detail")

    # دریافت تنظیمات هزینه ارسال از دیتابیس (تعریف شده در پنل ادمین)
    shipping_setting = ShippingSetting.load()

    user_addresses = list(
        request.user.addresses.select_related("province", "city").all()
    )
    selected_address = next(
        (addr for addr in user_addresses if addr.is_default),
        user_addresses[0] if user_addresses else None,
    )

    if request.method == "POST":
        selected_address_id = request.POST.get("selected_address_id")

        if selected_address_id and selected_address_id != "new" and selected_address_id.isdigit():
            addr_instance = get_object_or_404(
                Address, id=int(selected_address_id), user=request.user
            )
            form = AddressForm(request.POST, instance=addr_instance)
        else:
            form = AddressForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    saved_address = form.save(commit=False)
                    saved_address.user = request.user

                    if not saved_address.pk:
                        saved_address.address_name = (
                            request.POST.get("address_name")
                            or f"آدرس {len(user_addresses) + 1}"
                        )
                        if not user_addresses:
                            saved_address.is_default = True

                    saved_address.save()

                    cart_items = list(cart)
                    if not cart_items:
                        return redirect("cart:cart_detail")

                    for item in cart_items:
                        variant = item["variant"]
                        if variant.stock < item["quantity"]:
                            raise ValueError(
                                f"موجودی محصول «{variant.product.name} ({variant.color})» کافی نیست. (موجودی فعلی: {variant.stock})"
                            )

                    full_address_str = (
                        f"استان {saved_address.province.name}، "
                        f"شهر {saved_address.city.name}، {saved_address.address}"
                    )

                    # محاسبه دقیق هزینه ارسال بر اساس استان انتخاب‌شده (تهران یا شهرستان)
                    cart_total = cart.get_total_price()
                    shipping_cost = shipping_setting.calculate_cost(
                        saved_address.province.name, cart_total
                    )
                    total_payable = cart_total + shipping_cost

                    order = Order.objects.create(
                        user=request.user,
                        address=saved_address,
                        full_name=request.user.get_full_name() or request.user.phone_number,
                        phone_number=request.user.phone_number,
                        address_text=full_address_str,
                        postal_code=saved_address.postal_code,
                        shipping_cost=shipping_cost,
                        discount_amount=cart.get_total_discount(),
                        total_price=total_payable,
                        order_note=request.POST.get("order_note", "").strip(),
                    )

                    order_items = []
                    for item in cart_items:
                        variant = item["variant"]
                        size_str = f" - سایز: {variant.size}" if variant.size else ""
                        product_title = f"{variant.product.name} (رنگ: {variant.color}{size_str})"

                        order_items.append(
                            OrderItem(
                                order=order,
                                variant=variant,
                                product_name=product_title,
                                original_price=variant.price,
                                price=variant.final_price,
                                quantity=item["quantity"],
                            )
                        )

                    OrderItem.objects.bulk_create(order_items)

                return redirect("checkout:payment", order_id=order.id)

            except ValueError as e:
                form.add_error(None, str(e))

    else:
        form = AddressForm(instance=selected_address)

    # محاسبه اولیه هزینه ارسال برای نمایش در هنگام بارگذاری صفحه
    initial_province_name = (
        selected_address.province.name if (selected_address and selected_address.province) else ""
    )
    initial_shipping_cost = shipping_setting.calculate_cost(
        initial_province_name, cart.get_total_price()
    )

    context = {
        "cart": cart,
        "form": form,
        "user_addresses": user_addresses,
        "selected_address": selected_address,
        "shipping_setting": shipping_setting,
        "initial_shipping_cost": initial_shipping_cost,
        "initial_total_payable": cart.get_total_price() + initial_shipping_cost,
    }
    return render(request, "checkout/checkout.html", context)


@login_required(login_url="accounts:verify_otp")
def payment_request_view(request, order_id):
    """ارسال اطلاعات سفارش به زرین‌پال و دریافت Authority"""
    order = get_object_or_404(
        Order.objects.prefetch_related("items__variant__product"),
        id=order_id,
        user=request.user,
        is_paid=False,
    )

    for item in order.items.all():
        if not item.variant or item.variant.stock < item.quantity:
            return render(
                request,
                "checkout/payment_result.html",
                {
                    "order": order,
                    "success": False,
                    "error_message": f"متاسفانه موجودی محصول «{item.product_name}» به پایان رسیده است.",
                },
            )

    callback_url = request.build_absolute_uri(reverse("checkout:payment_verify"))

    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": int(order.total_price),
        "currency": "IRT",
        "description": f"پرداخت سفارش شماره #{order.id} از فروشگاه گره گره",
        "callback_url": callback_url,
        "metadata": {
            "mobile": order.phone_number,
        },
    }

    try:
        response = requests.post(
            ZP_API_REQUEST,
            json=payload,
            headers={"accept": "application/json", "content-type": "application/json"},
            timeout=10,
        )
        res_data = response.json()

        if res_data.get("data") and res_data["data"].get("code") == 100:
            authority = res_data["data"]["authority"]
            order.authority = authority
            order.status = Order.StatusChoices.PENDING
            order.save(update_fields=["authority", "status", "updated_at"])
            return redirect(f"{ZP_API_STARTPAY}{authority}")

        error_msg = res_data.get("errors", {}).get(
            "message", "خطا در برقراری ارتباط با درگاه زرین‌پال."
        )
        return render(
            request,
            "checkout/payment_result.html",
            {"order": order, "success": False, "error_message": error_msg},
        )

    except requests.exceptions.RequestException:
        return render(
            request,
            "checkout/payment_result.html",
            {
                "order": order,
                "success": False,
                "error_message": "عدم دسترسی به سرور درگاه پرداخت. لطفاً اتصال اینترنت خود را بررسی کنید.",
            },
        )


def payment_verify_view(request):
    """
    بازگشت کاربر از درگاه زرین‌پال و اعتبارسنجی نهایی تراکنش.
    نکته مهم: بدون @login_required تا در صورت عدم ارسال کوکی سشن در ریدایرکت شاپرک، تراکنش نسوزد.
    """
    authority = request.GET.get("Authority")
    status = request.GET.get("Status")

    if not authority:
        return redirect("home:home")

    order = get_object_or_404(Order, authority=authority)

    if order.is_paid:
        return render(
            request,
            "checkout/payment_result.html",
            {"order": order, "success": True, "already_verified": True},
        )

    if status != "OK":
        order.status = Order.StatusChoices.CANCELED
        order.save(update_fields=["status", "updated_at"])
        return render(
            request,
            "checkout/payment_result.html",
            {
                "order": order,
                "success": False,
                "error_message": "پرداخت توسط شما لغو شد یا با خطا مواجه گردید.",
            },
        )

    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": int(order.total_price),
        "authority": authority,
    }

    try:
        response = requests.post(
            ZP_API_VERIFY,
            json=payload,
            headers={"accept": "application/json", "content-type": "application/json"},
            timeout=10,
        )
        res_data = response.json()
        data = res_data.get("data", {}) if isinstance(res_data.get("data"), dict) else {}
        code = data.get("code")

        if code in (100, 101):
            with transaction.atomic():
                locked_order = Order.objects.select_for_update().get(pk=order.pk)
                if locked_order.is_paid:
                    return render(
                        request,
                        "checkout/payment_result.html",
                        {"order": locked_order, "success": True, "already_verified": True},
                    )

                order_items = list(locked_order.items.all())
                variant_ids = [item.variant_id for item in order_items if item.variant_id]
                locked_variants = {
                    v.id: v
                    for v in ProductVariant.objects.filter(id__in=variant_ids)
                    .order_by("id")
                    .select_for_update()
                }

                for item in order_items:
                    variant = locked_variants.get(item.variant_id)
                    if variant:
                        variant.stock = max(0, variant.stock - item.quantity)
                        variant.save(update_fields=["stock"])

                ref_id = str(data.get("ref_id", ""))
                locked_order.mark_as_paid(ref_id=ref_id)
                order = locked_order

            cart = Cart(request)
            cart.clear()

            return render(
                request,
                "checkout/payment_result.html",
                {"order": order, "success": True},
            )
        else:
            order.status = Order.StatusChoices.CANCELED
            order.save(update_fields=["status", "updated_at"])
            errors = res_data.get("errors", {})
            error_msg = (
                errors.get("message", "تراکنش توسط بانک تایید نشد.")
                if isinstance(errors, dict)
                else "تراکنش توسط بانک تایید نشد."
            )
            return render(
                request,
                "checkout/payment_result.html",
                {"order": order, "success": False, "error_message": error_msg},
            )

    except requests.exceptions.RequestException:
        return render(
            request,
            "checkout/payment_result.html",
            {
                "order": order,
                "success": False,
                "error_message": "خطا در تایید تراکنش از سمت درگاه. در صورت کسر وجه، مبلغ ظرف ۷۲ ساعت به حساب شما بازمی‌گردد.",
            },
        )


@login_required(login_url="accounts:verify_otp")
def track_order_view(request, order_id=None):
    """ویوی پیگیری وضعیت سفارش با شماره سفارش یا لینک مستقیم"""
    query_id = order_id or request.GET.get("order_id", "").strip().replace("#", "")
    order = None
    error_message = None

    base_qs = (
        Order.objects.filter(user=request.user)
        .select_related("address__province", "address__city")
        .prefetch_related("items__variant__product")
    )

    if query_id:
        if str(query_id).isdigit():
            order = base_qs.filter(id=int(query_id)).first()
            if not order:
                error_message = f"سفارشی با شماره #{query_id} در حساب کاربری شما یافت نشد."
        else:
            error_message = "لطفاً شماره سفارش را به صورت عدد وارد کنید."
    else:
        order = base_qs.first()

    is_tehran = False
    if order:
        if order.address and order.address.province and "تهران" in order.address.province.name:
            is_tehran = True
        elif "تهران" in order.address_text:
            is_tehran = True

    context = {
        "order": order,
        "query_id": query_id,
        "error_message": error_message,
        "is_tehran": is_tehran,
    }
    return render(request, "checkout/track_order.html", context)