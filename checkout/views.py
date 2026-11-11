import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction

from accounts.models import Address
from accounts.forms import AddressForm
from products.models import ProductVariant
from cart.cart_module import Cart
from .models import Order, OrderItem

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

                    # ۲. بررسی اولیه موجودی انبار قبل از ثبت سفارش
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
                        full_name=request.user.get_full_name() or request.user.phone_number,
                        phone_number=request.user.phone_number,
                        address_text=full_address_str,
                        postal_code=saved_address.postal_code,
                        total_price=cart.get_total_price(),
                        order_note=request.POST.get("order_note", ""),
                    )

                    # ۴. ثبت یکجای آیتم‌های سفارش (Bulk Create)
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
                                price=variant.final_price,
                                quantity=item["quantity"],
                            )
                        )

                    OrderItem.objects.bulk_create(order_items)

                # هدایت کاربر به ویوی اتصال به درگاه زرین‌پال
                return redirect("checkout:payment", order_id=order.id)

            except ValueError as e:
                form.add_error(None, str(e))
    
    else:
        form = AddressForm(instance=selected_address)

    context = {
        "cart": cart,
        "form": form,
        "user_addresses": user_addresses,
        "selected_address": selected_address,
    }
    return render(request, "checkout/checkout.html", context)


@login_required
def payment_request_view(request, order_id):
    """ارسال اطلاعات سفارش به زرین‌پال و دریافت Authority"""
    order = get_object_or_404(
        Order, id=order_id, user=request.user, is_paid=False
    )

    callback_url = request.build_absolute_uri(reverse("checkout:payment_verify"))

    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": int(order.total_price),
        "currency": "IRT",  # واحد تومان؛ نیازی به ضرب در ۱۰ نیست
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

        # کد 100 در زرین‌پال به معنای ایجاد موفق تراکنش است
        if res_data.get("data") and res_data["data"].get("code") == 100:
            authority = res_data["data"]["authority"]
            # ذخیره کد Authority در سفارش برای شناسایی در زمان بازگشت از بانک
            order.authority = authority
            order.save(update_fields=["authority"])
            return redirect(f"{ZP_API_STARTPAY}{authority}")

        error_msg = res_data.get("errors", {}).get("message", "خطا در برقراری ارتباط با درگاه زرین‌پال.")
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


@login_required
def payment_verify_view(request):
    """بازگشت کاربر از درگاه زرین‌پال و اعتبارسنجی نهایی تراکنش"""
    authority = request.GET.get("Authority")
    status = request.GET.get("Status")

    if not authority:
        return redirect("home:home")

    order = get_object_or_404(Order, authority=authority, user=request.user)

    # اگر سفارش قبلاً تایید شده باشد (جلوگیری از رفرش صفحه توسط کاربر)
    if order.is_paid:
        return render(
            request,
            "checkout/payment_result.html",
            {"order": order, "success": True, "already_verified": True},
        )

    # اگر کاربر دکمه انصراف را زده باشد یا پرداخت ناموفق بوده باشد
    if status != "OK":
        order.status = Order.StatusChoices.CANCELED
        order.save(update_fields=["status"])
        return render(
            request,
            "checkout/payment_result.html",
            {
                "order": order,
                "success": False,
                "error_message": "پرداخت توسط شما لغو شد یا با خطا مواجه گردید.",
            },
        )

    # ارسال درخواست تایید نهایی به زرین‌پال
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
        data = res_data.get("data", {})
        code = data.get("code")

        # کد 100 (موفق) و کد 101 (قبلاً تایید شده)
        if code in (100, 101):
            with transaction.atomic():
                # کسر موجودی انبار برای هر تنوع محصول با قفل ردیف دیتابیس
                for item in order.items.select_related("variant"):
                    if item.variant:
                        variant = ProductVariant.objects.select_for_update().get(pk=item.variant.pk)
                        if variant.stock >= item.quantity:
                            variant.stock -= item.quantity
                            variant.save(update_fields=["stock"])
                        else:
                            # اگر در فاصله رفتن به درگاه موجودی تمام شده باشد
                            variant.stock = 0
                            variant.save(update_fields=["stock"])

                # بروزرسانی وضعیت سفارش و ذخیره کد رهگیری
                order.is_paid = True
                order.status = Order.StatusChoices.PAID
                order.ref_id = str(data.get("ref_id", ""))
                order.save(update_fields=["is_paid", "status", "ref_id"])

                # خالی کردن سبد خرید پس از پرداخت موفق
                cart = Cart(request)
                cart.clear()

            return render(
                request,
                "checkout/payment_result.html",
                {"order": order, "success": True},
            )
        else:
            order.status = Order.StatusChoices.CANCELED
            order.save(update_fields=["status"])
            error_msg = res_data.get("errors", {}).get("message", "تراکنش توسط بانک تایید نشد.")
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


def track_order_view(request, order_id=None):
    if not request.user.is_authenticated:
        return redirect("accounts:verify_otp")
    """ویوی پیگیری وضعیت سفارش با شماره سفارش یا لینک مستقیم"""
    # دریافت شماره سفارش از URL یا از فرم جستجو (GET)
    query_id = order_id or request.GET.get("order_id", "").strip().replace("#", "")
    order = None
    error_message = None

    if query_id:
        if str(query_id).isdigit():
            order = (
                Order.objects.filter(id=int(query_id), user=request.user)
                .select_related("address__province", "address__city")
                .prefetch_related("items__variant__product")
                .first()
            )
            if not order:
                error_message = f"سفارشی با شماره #{query_id} در حساب کاربری شما یافت نشد."
        else:
            error_message = "لطفاً شماره سفارش را به صورت عدد وارد کنید."
    else:
        # اگر کاربر بدون شماره سفارش وارد صفحه شد، آخرین سفارش او را به صورت پیش‌فرض نمایش بده
        order = (
            Order.objects.filter(user=request.user)
            .select_related("address__province", "address__city")
            .prefetch_related("items__variant__product")
            .first()
        )

    # تشخیص تهران یا شهرستان برای نمایش زمان تحویل
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