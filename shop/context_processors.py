from .models import CartItem

def cart_item_count(request):
    count = 0
    if request.user.is_authenticated:
        # Only count items for authenticated users
        count = CartItem.objects.filter(user=request.user).count()
    return {'cart_item_count': count}