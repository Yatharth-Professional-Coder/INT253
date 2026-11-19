from django import forms
from .models import Product, Supplier, Category, Customer, Purchase, StockMovement

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'barcode', 'category', 'supplier', 'cost_price', 'selling_price', 'current_stock', 'min_stock_level', 'unit', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Wireless Ergonomic Mouse'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ELEC-MOU-001'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scan or enter barcode'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'current_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'min_stock_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Product specifications, size, notes...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_name', 'phone', 'email', 'address', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company or Vendor Name'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sales Rep or Contact Person'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 (555) 000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'orders@supplier.com'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Warehouse/Office address'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Terms, payment conditions, notes'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Category description'}),
        }


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer Full Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Customer address'}),
        }


class StockAdjustmentForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    movement_type = forms.ChoiceField(
        choices=[
            ('adjustment', 'Manual Correction / Audit'),
            ('damage', 'Damaged / Expired Goods'),
            ('return', 'Customer Return'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity_change = forms.IntegerField(
        help_text="Use positive (+) to add stock, negative (-) to deduct stock",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +5 or -2'})
    )
    reference_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Audit #, Ticket # or Memo'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Reason for adjustment'})
    )


class UserCreateForm(forms.Form):
    ROLE_CHOICES = [
        ('admin', 'Super Admin (Full System & User Control)'),
        ('manager', 'Manager / Staff (Inventory & Purchases)'),
        ('cashier', 'Cashier (POS Billing & Sales Access)'),
    ]

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter unique username'})
    )
    first_name = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'user@smartstock.local'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create strong password'})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.BooleanField(
        required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class UserEditForm(forms.Form):
    ROLE_CHOICES = [
        ('admin', 'Super Admin (Full System & User Control)'),
        ('manager', 'Manager / Staff (Inventory & Purchases)'),
        ('cashier', 'Cashier (POS Billing & Sales Access)'),
    ]

    first_name = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'user@smartstock.local'})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to keep existing password'}),
        help_text="Only fill this if you want to reset this user's password."
    )


