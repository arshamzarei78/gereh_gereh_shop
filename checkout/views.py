from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.models import Address
from accounts.forms import AddressForm
from cart.cart_module import Cart

@login_required
def checkout_view(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('cart:cart_detail')

    # گرفتن تمام آدرس‌های کاربر
    user_addresses = request.user.addresses.select_related('province', 'city').all()
    
    # پیدا کردن آدرس پیش‌فرض (یا اولین آدرس موجود اگر پیش‌فرضی نبود)
    selected_address = user_addresses.filter(is_default=True).first() or user_addresses.first()

    if request.method == 'POST':
        # بررسی اینکه آیا کاربر تیک «ذخیره به عنوان آدرس جدید» را زده یا می‌خواهد قبلی را ویرایش کند
        selected_address_id = request.POST.get('selected_address_id')

        if selected_address_id != 'new':
            addr_instance = get_object_or_404(Address, id=selected_address_id, user=request.user)
            form = AddressForm(request.POST, instance=addr_instance)
        else:
            # حالت ۲: کاربر می‌خواهد اطلاعات فرم به عنوان یک آدرس جدید به اکانتش اضافه شود
            form = AddressForm(request.POST)

        if form.is_valid():
            saved_address = form.save(commit=False)
            saved_address.user = request.user
            
            # اگر آدرس جدید است، نام آن را تنظیم کن
            if not saved_address.pk:
                saved_address.address_name = request.POST.get('address_name') or f"آدرس {user_addresses.count() + 1}"
                if not user_addresses.exists():
                    saved_address.is_default = True
            
            saved_address.save()

            # =========================================================
            # در اینجا سفارش (Order) را با استفاده از saved_address ثبت کنید
            # و کاربر را به درگاه پرداخت بفرستید
            # =========================================================
            
            return redirect('checkout:payment') # یا هر آدرسی که برای ثبت نهایی دارید
    else:
        # در حالت باز شدن صفحه، اطلاعات آدرس پیش‌فرض را داخل فیلدها می‌نشانیم
        form = AddressForm(instance=selected_address)

    context = {
        'cart': cart,
        'form': form,
        'user_addresses': user_addresses,
        'selected_address': selected_address,
    }
    return render(request, 'checkout/checkout.html', context)