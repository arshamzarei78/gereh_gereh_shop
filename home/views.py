from django.shortcuts import render
from django.views.generic import TemplateView
from products.models import Product
from blog.models import Post

class HomeView(TemplateView):
    template_name = 'home/home.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all()[:5]
        context['posts'] = Post.objects.all()
        return context

class FaqView(TemplateView):
    template_name = 'home/faq.html'

class ContactUsView(TemplateView):
    template_name = 'home/contact_us.html'