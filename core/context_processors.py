from orders.models import Cart, CartItem

def cart_count(request):
    """Передает количество товаров в корзине в каждый шаблон"""
    count = 0
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
        count = cart.items.count()
    return {'cart_count': count}