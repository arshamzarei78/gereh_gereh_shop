
from .cart_module import Cart  # فرض بر این است که کلاس Cart را در cart.py دارید

def cart(request):
    return {'cart': Cart(request)}