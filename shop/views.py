from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Product, CartItem
from .models import Product, CartItem, Order, OrderItem, DiscountRule
from django.db.models import Sum, F
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .forms import ProductForm

def home(request):
    featured_products = Product.objects.filter(is_featured=True)
    return render(request, 'home.html', {'products': featured_products})

def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})


@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Use filter() to find existing items.
    existing_cart_items = CartItem.objects.filter(user=request.user, product=product)

    if existing_cart_items.exists():
        # If items exist, get the first one and increment its quantity.
        cart_item = existing_cart_items.first()
        cart_item.quantity += 1
        cart_item.save()

        # Delete any duplicate entries to clean up the database.
        existing_cart_items.exclude(id=cart_item.id).delete()
    else:
        # If no items exist, create a new one.
        CartItem.objects.create(
            user=request.user,
            product=product,
            quantity=1
        )

    return redirect('cart')

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'subtotal': subtotal})

@login_required
def remove_from_cart(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, user=request.user)
    cart_item.delete()
    return redirect('cart')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
        if 'next' in request.GET:
            messages.info(request, "You must be logged in to view this page.")
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def apply_discount(request):
    if request.method == 'POST':
        code = request.POST.get('discount_code')
        try:
            discount = DiscountRule.objects.get(
                code=code,
                active=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            )
            request.session['discount_id'] = discount.id
            messages.success(request, f"Discount code '{code}' applied successfully!")
        except DiscountRule.DoesNotExist:
            request.session['discount_id'] = None
            messages.error(request, "Invalid or expired discount code.")
            
    return redirect('cart')

# Update your checkout view to apply the discount when placing an order
@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    if not cart_items:
        return redirect('cart')

    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    
    discount_id = request.session.get('discount_id')
    discount_applied = None
    if discount_id:
        try:
            discount_applied = DiscountRule.objects.get(id=discount_id)
            discount_amount = (subtotal * discount_applied.discount_percent) / 100
            total_amount = subtotal - discount_amount
        except DiscountRule.DoesNotExist:
            total_amount = subtotal
            messages.error(request, "The discount code is no longer valid.")
    else:
        total_amount = subtotal

    if request.method == 'POST':
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                total_amount=total_amount,
                status='pending',
                discount_applied=discount_applied # Save the applied discount to the order [cite: 11]
            )
            
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.product.price
                )
            
            cart_items.delete()
            if 'discount_id' in request.session:
                del request.session['discount_id']
                
        return redirect('order_confirmation', order_id=order.id)
    
    return render(
        request, 
        'checkout.html', 
        {'cart_items': cart_items, 'subtotal': subtotal, 'total_amount': total_amount, 'discount_applied': discount_applied}
    )


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_confirmation.html', {'order': order})

@login_required
def orders_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at').prefetch_related('items__product')
    return render(request, 'orders_list.html', {'orders': orders})

@login_required
def increase_quantity(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, user=request.user)
    cart_item.quantity += 1
    cart_item.save()
    return redirect('cart')

@login_required
def decrease_quantity(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, user=request.user)
    cart_item.quantity -= 1
    
    if cart_item.quantity <= 0:
        cart_item.delete()
    else:
        cart_item.save()
        
    return redirect('cart')
@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, f"Product '{product.name}' was successfully deleted.")
        return redirect('product_list') # Redirect to the product list page after deletion
    
    # If a GET request is made, show a confirmation page
    return render(request, 'product_confirm_delete.html', {'product': product})

def search_products(request):
    query = request.GET.get('q') # Get the query from the URL parameter 'q'
    
    products = Product.objects.all()
    
    if query:
        # Display the received query for debugging purposes
        messages.info(request, f"Searching for: '{query}'")
        
        # Filter products where the name or description contains the query
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    else:
        messages.warning(request, "No search query provided. Showing all products.")
        
    return render(request, 'product_list.html', {'products': products, 'query': query})

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        # If the form is submitted, bind the POST data and files to the form
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated successfully!")
            # Redirect to the product detail page after saving
            return redirect('product_detail', pk=product.pk)
    else:
        # If it's a GET request, create a form instance populated with the product's data
        form = ProductForm(instance=product)
        
    return render(request, 'product_edit.html', {'form': form, 'product': product})

def product_category(request, category_slug):
    # Filter products by the category field
    products = Product.objects.filter(category=category_slug)
    
    # Capitalize and format the category name for display
    #.title() capitalizes the first letter of each word, so "men t shirts" becomes "Men T Shirts"
    display_category_name = category_slug.replace('-', ' ').title()
    
    return render(request, 'product_list.html', {'products': products, 'category': display_category_name})