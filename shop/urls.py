from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('remove-from-cart/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('my-orders/', views.orders_list, name='orders_list'),
    path('apply-discount/', views.apply_discount, name='apply_discount'),
    path('increase-quantity/<int:pk>/', views.increase_quantity, name='increase_quantity'),
    path('decrease-quantity/<int:pk>/', views.decrease_quantity, name='decrease_quantity'),
    path('product/<int:pk>/delete/', views.delete_product, name='delete_product'),
    path('search/', views.search_products, name='search_products'),
    path('product/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('category/<str:category_slug>/', views.product_category, name='product_category'),
]