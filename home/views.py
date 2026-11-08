from django.shortcuts import render
from django.views.generic import TemplateView
from products.models import Product
from blog.models import Post
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import ContactMessage
from .forms import ContactForm


class ContactUsView(CreateView):
    model = ContactMessage
    form_class = ContactForm
    template_name = "home/contact_us.html" 
    success_url = reverse_lazy("home:contact_us")

    def get_initial(self):
        """پیش‌پر کردن فیلدهای فرم در صورتی که کاربر لاگین باشد"""
        initial = super().get_initial()
        user = self.request.user
        if user.is_authenticated:
            initial["full_name"] = user.get_full_name()
            initial["phone_number"] = user.phone_number
            initial["email"] = user.email
        return initial

    def form_valid(self, form):
        messages.success(
            self.request,
            "پیام شما با موفقیت ثبت شد. کارشناسان «گره گره» به زودی با شما تماس خواهند گرفت.",
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "لطفاً خطاهای موجود در فرم را بررسی و مجدداً تلاش کنید.",
        )
        return super().form_invalid(form)

class HomeView(TemplateView):
    template_name = 'home/home.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all()[:5]
        context['posts'] = Post.objects.all()
        return context

class FaqView(TemplateView):
    template_name = 'home/faq.html'

