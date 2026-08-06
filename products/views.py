from django.shortcuts import render
from django.views.generic import DetailView
from .models import Product
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import ProductVariant


class PtoductView(DetailView):
    model = Product
