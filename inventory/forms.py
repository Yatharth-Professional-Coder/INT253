from django import forms
from .models import Product, Supplier, Category, Customer, Purchase, StockMovement, Store

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'barcode', 'category', 'supplier',
            'cost_price', 'selling_price', 'current_stock', 'min_stock_level',
            'unit', 'description', 'has_expiry', 'expiry_date', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Tata Salt Vacuum Evaporated 1kg'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. GRO-TAT-001'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scan or enter barcode (e.g. 8901030383721)'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'current_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'min_stock_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Product specifications, pack size, ingredients, notes...'}),
            'has_expiry': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_has_expiry', 'role': 'switch'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_expiry_date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        has_expiry = cleaned_data.get('has_expiry')
        expiry_date = cleaned_data.get('expiry_date')

        if has_expiry:
            if not expiry_date:
                self.add_error('expiry_date', 'Please provide an expiry date, or toggle off expiry tracking.')
        else:
            cleaned_data['expiry_date'] = None
        return cleaned_data


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_name', 'phone', 'email', 'address', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company or Vendor Name (e.g. Apex Enterprises Pvt Ltd)'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sales Rep or Contact Person (e.g. Rahul Sharma)'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'orders@apexenterprises.in'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'e.g. Plot 45, Okhla Industrial Area Phase-III, New Delhi 110020'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Payment terms, GSTIN: 07AAAAA0000A1Z5, credit period'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Kirana & Grocery, Electronics, Dairy & Snacks'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Category specifications or description'}),
        }


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer Full Name (e.g. Amit Kumar)'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'customer@gmail.com'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'e.g. Flat 302, Shanti Kunj, Sector 62, Noida, UP'}),
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


class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['name', 'code', 'manager_name', 'phone', 'email', 'address', 'city', 'is_main', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Connaught Place Flagship Store'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. STR-DEL-01'}),
            'manager_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Branch Manager Name (e.g. Vikramaditya Singh)'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'delhi.cp@smartstock.in'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Shop 12, Block B, Inner Circle, Connaught Place'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'New Delhi, Delhi'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserCreateForm(forms.Form):
    ROLE_CHOICES = [
        ('admin', 'Website Owner / Super Admin (Full Control)'),
        ('store_admin', 'Store Admin / Multi-Branch Manager (Can Add & Modify Stores)'),
        ('manager', 'Store Manager / Supervisor'),
        ('cashier', 'POS Cashier'),
    ]

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter unique username'})
    )
    first_name = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name (e.g. Aarav)'})
    )
    last_name = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name (e.g. Patel)'})
    )
    phone = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'employee@smartstock.in'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create strong password'})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'userRoleSelect'})
    )
    assigned_store = forms.ModelChoiceField(
        queryset=Store.objects.all(),
        required=False,
        empty_label="All Stores / HQ Floating",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.BooleanField(
        required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    # Granular Access Control Managed by Website Owner
    can_manage_stores = forms.BooleanField(
        required=False, initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_access_pos = forms.BooleanField(
        required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_manage_products = forms.BooleanField(
        required=False, initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_manage_suppliers = forms.BooleanField(
        required=False, initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_view_reports = forms.BooleanField(
        required=False, initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_adjust_stock = forms.BooleanField(
        required=False, initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class UserEditForm(forms.Form):
    ROLE_CHOICES = [
        ('admin', 'Website Owner / Super Admin (Full Control)'),
        ('store_admin', 'Store Admin / Multi-Branch Manager (Can Add & Modify Stores)'),
        ('manager', 'Store Manager / Supervisor'),
        ('cashier', 'POS Cashier'),
    ]

    first_name = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name (e.g. Aarav)'})
    )
    last_name = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name (e.g. Patel)'})
    )
    phone = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'employee@smartstock.in'})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'userRoleSelect'})
    )
    assigned_store = forms.ModelChoiceField(
        queryset=Store.objects.all(),
        required=False,
        empty_label="All Stores / HQ Floating",
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

    # Granular Access Control Managed by Website Owner
    can_manage_stores = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_access_pos = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_manage_products = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_manage_suppliers = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_view_reports = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_adjust_stock = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


