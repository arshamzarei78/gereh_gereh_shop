from django.shortcuts import render,redirect
from django.utils import timezone
from django.views.generic import TemplateView ,FormView ,CreateView
from django.views import View
from django.contrib.auth import authenticate , login , logout
from .models import User
from django.db import transaction
from .forms import RegisterForm , AddressForm , VerifyOTPForm , SendOTPForm
from django.urls import reverse_lazy
from django.http import JsonResponse
from iranian_cities.models import City
import secrets
from django.http import HttpResponseRedirect


class SendOTPView(View):

    def post(self, request):

        form = SendOTPForm(request.POST)
        if not form.is_valid():
            return JsonResponse(
                {
                    "status": "error",
                    "message": "شماره موبایل معتبر نیست.",
                },
                status=400,
            )

     
        last_sent = request.session.get("otp_last_sent")

        if last_sent:
            elapsed = timezone.now().timestamp() - last_sent
            if elapsed < 60:
                remaining = 60 - int(elapsed)

                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"لطفاً {remaining} ثانیه دیگر دوباره تلاش کنید.",
                    },
                    status=429,
                )

        phone_number = form.cleaned_data["phone_number"]

        code = str(secrets.randbelow(900000) + 100000)

        request.session["otp"] = str(code)
        request.session["phone_number"] = phone_number
        request.session["otp_last_sent"] = timezone.now().timestamp()
        request.session["otp_attempts"] = 0

        print(code)
        print(phone_number)

        return JsonResponse({"status": "success"})


class VerifyOTPView(FormView):
    
    form_class = VerifyOTPForm
    template_name = "accounts/verify.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home:home")
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        phone_number = self.request.session.get("phone_number", "")
        return self.render_to_response(
            self.get_context_data(form=form, phone_number=phone_number)
        )

    def form_valid(self, form):
        code = form.cleaned_data["code"]
        otp = self.request.session.get("otp")
        last_sent = self.request.session.get("otp_last_sent", 0)
        attempts = self.request.session.get("otp_attempts", 0)

        if code != otp:
            form.add_error("code", "کد وارد شده صحیح نیست")
            self.request.session['otp_attempts'] = attempts +1
            return self.form_invalid(form)

        if timezone.now().timestamp() - last_sent > 120:
            form.add_error("code", "کد تایید منقضی شده است. لطفاً مجدداً درخواست دهید.")
            return self.form_invalid(form)

        phone_number = self.request.session.get("phone_number")
        user = User.objects.filter(phone_number=phone_number).first()

        # کاربر قبلاً ثبت‌نام کرده
        if user:
            login(self.request, user)
            
            self.request.session.pop("otp", None)
            self.request.session.pop("phone_number", None)
            self.request.session.pop("otp_last_sent", None)

            cart = self.request.session.get('cart')
            if cart:
                return redirect("checkout:checkout")
            else:
                return redirect("home:home")

        # کاربر جدید
        self.request.session["is_phone_verified"] = True
        cart = self.request.session.get("cart")
        if cart:
            return redirect("checkout:checkout")
        return redirect("accounts:register")


class RegisterView(FormView):
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("home:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home:home")
        
        verified = request.session.get('is_phone_verified')
        phone_number = self.request.session.get("phone_number")
        if not phone_number or not verified:
            return redirect("accounts:verify_otp")
        
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["phone_number"] = self.request.session.get("phone_number")
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "address_form" not in context:
            if self.request.method == "POST":
                context["address_form"] = AddressForm(self.request.POST)
            else:
                context["address_form"] = AddressForm()
        return context

    def post(self, request, *args, **kwargs):

        phone_number = request.session.get("phone_number")
        post_data = request.POST.copy()
        post_data["phone_number"] = phone_number

        form = RegisterForm(post_data)
        
        address_form = AddressForm(post_data)

        if form.is_valid() and address_form.is_valid():
            return self.form_valid(form, address_form)
        else:
            return self.form_invalid(form, address_form)

    def form_valid(self, form, address_form):
        try:
            phone_number = self.request.session.get("phone_number")

            with transaction.atomic():
                user = form.save(commit=False)
                user.phone_number = phone_number
                user.set_unusable_password()
                user.save()

                address = address_form.save(commit=False)
                address.user = user
                address.address_name = "آدرس اصلی"
                address.is_default = True
                address.save()

            self.request.session.pop("phone_number", None)
            self.request.session.pop("otp", None)

            login(self.request, user)

            cart = self.request.session.get("cart")
            if cart:
                return redirect("checkout:checkout")
            return redirect("home:home")

        except Exception as e:
            form.add_error(None, f"خطایی در ذخیره‌سازی رخ داد: {e}")
            return self.render_to_response(
                self.get_context_data(form=form, address_form=address_form)
            )

    def form_invalid(self, form, address_form=None):
        if address_form is None:
            address_form = AddressForm(self.request.POST)

        return self.render_to_response(
            self.get_context_data(form=form, address_form=address_form))

    
def load_cities(request):

    province_id = request.GET.get("province")
    if not province_id or not province_id.isdigit():
        return JsonResponse([], safe=False)

    cities = City.objects.filter(
        province_id=province_id,
        city_type=0
    ).values(
        "id",
        "name"
    ).order_by("name")

    return JsonResponse(
        list(cities),
        safe=False
    )