from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'inventory_count', 'image', 'category']









# This file defines a Django ModelForm for your Product model.

# Why is it needed?

# It lets you easily create and validate forms for adding or editing products.
# It automatically generates form fields for the specified model fields (name, description, price, etc.).
# It handles form validation and saving data to the database.
# Summary:
# forms.py makes working with product forms in your views and templates easier, more secure, and less error-prone.