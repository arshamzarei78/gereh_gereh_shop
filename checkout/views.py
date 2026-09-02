from django.shortcuts import render
from django.views.generic import TemplateView

class Checkout(TemplateView):
    template_name = 'checkout/checkout.html'