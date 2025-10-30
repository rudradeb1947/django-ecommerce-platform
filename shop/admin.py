from django.contrib import admin
from .models import Product, DiscountRule, CartItem, Order, OrderItem

admin.site.register(Product)
admin.site.register(DiscountRule)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)