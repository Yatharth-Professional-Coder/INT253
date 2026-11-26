import json
from functools import wraps
from decimal import Decimal
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, F, Q, Avg
from django.db.models.functions import TruncDate

from .models import Category, Supplier, Product, Customer, Purchase, PurchaseItem, Sale, SaleItem, StockMovement, UserProfile, Store
from .forms import (
    ProductForm, SupplierForm, CategoryForm, CustomerForm, 
    StockAdjustmentForm, UserCreateForm, UserEditForm, StoreForm
)
from .services import process_pos_sale, process_purchase_order, manual_stock_adjustment, generate_invoice_number

def superuser_required(view_func):
    """Decorator to restrict access strictly to Website Owner / Super Admin accounts."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser:
            messages.error(request, "Access restricted: Only the Website Owner (Super Admin) can manage access permissions and user accounts.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

def store_admin_required(view_func):
    """Decorator allowing Store Admin with store management privileges."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser:
            return redirect('user_list')
        if hasattr(request.user, 'profile') and request.user.profile.can_manage_stores:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Access restricted: You need Store Administrator privileges to add or modify stores.")
        return redirect('dashboard')
    return wrapper

# ==========================================
# AUTHENTICATION VIEWS
# ==========================================
def login_view(request):
    """Clean, modern user login portal."""
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('user_list')
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url and next_url != 'dashboard':
                    return redirect(next_url)
                if user.is_superuser:
                    return redirect('user_list')
                return redirect('dashboard')
            else:
                messages.error(request, "This account is inactive. Please contact a Super Administrator.")
        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, 'inventory/login.html')


def logout_view(request):
    """User logout endpoint."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def dashboard(request):
    """Main executive dashboard with real-time inventory and profit analytics."""
    if request.user.is_superuser:
        return redirect('user_list')

    today = timezone.now().date()
    start_of_today = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
    start_of_month = timezone.make_aware(timezone.datetime(today.year, today.month, 1))

    # Product metrics
    products = Product.objects.filter(is_active=True)
    total_products = products.count()
    low_stock_products = products.filter(current_stock__gt=0, current_stock__lte=F('min_stock_level'))
    out_of_stock_products = products.filter(current_stock__lte=0)
    
    # Inventory Valuation
    all_inventory = Product.objects.all()
    inventory_val_cost = sum(p.inventory_value_cost for p in all_inventory)
    inventory_val_retail = sum(p.inventory_value_retail for p in all_inventory)
    potential_profit = inventory_val_retail - inventory_val_cost

    # Sales & Revenue metrics
    today_sales = Sale.objects.filter(status='completed', sale_date__gte=start_of_today)
    today_revenue = today_sales.aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')
    today_profit = sum(sale.total_profit for sale in today_sales)

    month_sales = Sale.objects.filter(status='completed', sale_date__gte=start_of_month)
    month_revenue = month_sales.aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')
    month_profit = sum(sale.total_profit for sale in month_sales)

    all_sales = Sale.objects.filter(status='completed')
    total_revenue = all_sales.aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')
    total_sales_count = all_sales.count()

    # Total Purchases
    purchases = Purchase.objects.filter(status='received')
    total_purchases_amt = purchases.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    # Recent activity
    recent_sales = Sale.objects.filter(status='completed').order_by('-sale_date')[:6]
    recent_purchases = Purchase.objects.all().order_by('-purchase_date')[:6]
    critical_stock = list(out_of_stock_products[:5]) + list(low_stock_products[:5])

    # 7-day Sales Chart Data
    seven_days_ago = today - timedelta(days=6)
    daily_sales = (
        Sale.objects.filter(status='completed', sale_date__date__gte=seven_days_ago)
        .annotate(date=TruncDate('sale_date'))
        .values('date')
        .annotate(daily_total=Sum('grand_total'))
        .order_by('date')
    )
    
    chart_dates = []
    chart_revenue = []
    daily_map = {item['date'].strftime('%b %d'): float(item['daily_total']) for item in daily_sales}
    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        day_str = day.strftime('%b %d')
        chart_dates.append(day_str)
        chart_revenue.append(daily_map.get(day_str, 0.0))

    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_products.count(),
        'out_of_stock_count': out_of_stock_products.count(),
        'inventory_val_cost': inventory_val_cost,
        'inventory_val_retail': inventory_val_retail,
        'potential_profit': potential_profit,
        'today_revenue': today_revenue,
        'today_profit': today_profit,
        'month_revenue': month_revenue,
        'month_profit': month_profit,
        'total_revenue': total_revenue,
        'total_sales_count': total_sales_count,
        'total_purchases_amt': total_purchases_amt,
        'recent_sales': recent_sales,
        'recent_purchases': recent_purchases,
        'critical_stock': critical_stock[:8],
        'chart_dates_json': json.dumps(chart_dates),
        'chart_revenue_json': json.dumps(chart_revenue),
    }
    return render(request, 'inventory/dashboard.html', context)


# ==========================================
# POS / BILLING VIEWS
# ==========================================
@login_required
def pos_view(request):
    """Fast, interactive Point of Sale billing terminal."""
    if request.user.is_superuser:
        messages.info(request, "Website Owner accounts are dedicated exclusively to User Management and Access Control.")
        return redirect('user_list')
    if not (hasattr(request.user, 'profile') and request.user.profile.can_access_pos):
        messages.error(request, "Access Restricted: You do not have permission to access the POS Billing terminal. Please contact the Website Owner.")
        return redirect('dashboard')

    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True).select_related('category')
    customers = Customer.objects.all().order_by('name')
    context = {
        'categories': categories,
        'products': products,
        'customers': customers,
    }
    return render(request, 'inventory/pos.html', context)


def api_search_products(request):
    """JSON API for POS product search (by query, barcode, category)."""
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')

    products = Product.objects.filter(is_active=True)

    if category_id:
        products = products.filter(category_id=category_id)

    if q:
        products = products.filter(
            Q(name__icontains=q) |
            Q(sku__icontains=q) |
            Q(barcode__iexact=q)
        )

    data = [
        {
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'barcode': p.barcode or '',
            'category': p.category.name if p.category else 'General',
            'cost_price': float(p.cost_price),
            'selling_price': float(p.selling_price),
            'current_stock': p.current_stock,
            'unit': p.get_unit_display(),
            'is_out_of_stock': p.is_out_of_stock,
            'is_low_stock': p.is_low_stock,
        }
        for p in products[:40]
    ]
    return JsonResponse({'products': data})


def api_pos_checkout(request):
    """AJAX endpoint to finalize POS transaction with auto-stock updates."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        if not items:
            return JsonResponse({'success': False, 'error': 'Cart is empty.'}, status=400)

        customer_id = data.get('customer_id')
        customer = Customer.objects.filter(id=customer_id).first() if customer_id else None
        customer_name = data.get('customer_name', 'Walk-in Customer')
        customer_phone = data.get('customer_phone', '')
        payment_method = data.get('payment_method', 'cash')
        tax_rate = Decimal(str(data.get('tax_rate', 0)))
        discount_amount = Decimal(str(data.get('discount_amount', 0)))
        amount_paid = Decimal(str(data.get('amount_paid', 0)))
        notes = data.get('notes', '')
        cashier = data.get('cashier', 'Cashier 1')

        sale = process_pos_sale(
            items=items,
            customer=customer,
            customer_name=customer_name,
            customer_phone=customer_phone,
            tax_rate=tax_rate,
            discount_amount=discount_amount,
            amount_paid=amount_paid,
            payment_method=payment_method,
            cashier=cashier,
            notes=notes
        )

        return JsonResponse({
            'success': True,
            'invoice_id': sale.id,
            'invoice_number': sale.invoice_number,
            'grand_total': float(sale.grand_total),
            'amount_paid': float(sale.amount_paid),
            'change_amount': float(sale.change_amount),
            'message': 'Sale completed and inventory updated!'
        })

    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Transaction error: {str(e)}'}, status=500)


def api_quick_customer(request):
    """Quickly create a customer from POS screen."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            phone = data.get('phone', '').strip()
            if not name:
                return JsonResponse({'success': False, 'error': 'Customer name is required.'})
            customer = Customer.objects.create(
                name=name,
                phone=phone,
                email=data.get('email', '').strip(),
                address=data.get('address', '').strip()
            )
            return JsonResponse({'success': True, 'id': customer.id, 'name': customer.name, 'phone': customer.phone or ''})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'POST required'})


# ==========================================
# PRODUCT & INVENTORY VIEWS
# ==========================================
@login_required
def product_list(request):
    """View products with filtering, search, and stock level badges."""
    if request.user.is_superuser:
        return redirect('user_list')
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    stock_status = request.GET.get('status')

    products = Product.objects.select_related('category', 'supplier').all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(barcode__iexact=query)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if stock_status == 'low':
        products = products.filter(current_stock__gt=0, current_stock__lte=F('min_stock_level'))
    elif stock_status == 'out':
        products = products.filter(current_stock__lte=0)
    elif stock_status == 'in':
        products = products.filter(current_stock__gt=F('min_stock_level'))

    categories = Category.objects.all()

    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'selected_status': stock_status,
        'query': query,
    }
    return render(request, 'inventory/product_list.html', context)


@login_required
def product_create(request):
    """Add new product to catalog."""
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.can_manage_products)):
        messages.error(request, "Access Restricted: You do not have permission to add new products. Contact the Website Owner.")
        return redirect('product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            # If initial stock > 0, log it
            if product.current_stock > 0:
                StockMovement.objects.create(
                    product=product,
                    movement_type='adjustment',
                    quantity=product.current_stock,
                    previous_stock=0,
                    new_stock=product.current_stock,
                    reference_number="INITIAL-STOCK",
                    notes="Initial stock quantity on product creation"
                )
            messages.success(request, f"Product '{product.name}' created successfully!")
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Add New Product'})


@login_required
def product_update(request, pk):
    """Edit existing product."""
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.can_manage_products)):
        messages.error(request, "Access Restricted: You do not have permission to edit products. Contact the Website Owner.")
        return redirect('product_list')

    product = get_object_or_404(Product, pk=pk)
    old_stock = product.current_stock
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            updated_product = form.save()
            new_stock = updated_product.current_stock
            if old_stock != new_stock:
                StockMovement.objects.create(
                    product=updated_product,
                    movement_type='adjustment',
                    quantity=new_stock - old_stock,
                    previous_stock=old_stock,
                    new_stock=new_stock,
                    reference_number="MANUAL-EDIT",
                    notes="Stock updated via product edit form"
                )
            messages.success(request, f"Product '{updated_product.name}' updated successfully!")
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'inventory/product_form.html', {'form': form, 'title': f'Edit Product: {product.name}', 'product': product})


@login_required
def product_delete(request, pk):
    """Delete a product."""
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.can_manage_products)):
        messages.error(request, "Access Restricted: You do not have permission to delete products. Contact the Website Owner.")
        return redirect('product_list')
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f"Product '{name}' deleted successfully.")
        return redirect('product_list')
    return render(request, 'inventory/confirm_delete.html', {'object': product, 'type': 'Product'})


@login_required
def low_stock_view(request):
    """Dedicated Low-Stock Alerts Center."""
    if request.user.is_superuser:
        return redirect('user_list')
    low_stock_items = Product.objects.filter(
        current_stock__gt=0, 
        current_stock__lte=F('min_stock_level'), 
        is_active=True
    ).select_related('category', 'supplier').order_by('current_stock')

    out_of_stock_items = Product.objects.filter(
        current_stock__lte=0, 
        is_active=True
    ).select_related('category', 'supplier').order_by('name')

    context = {
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
    }
    return render(request, 'inventory/low_stock_alerts.html', context)


# ==========================================
# SUPPLIER & PURCHASES VIEWS
# ==========================================
@login_required
def supplier_list(request):
    """Suppliers list with purchase count & total amount."""
    if request.user.is_superuser:
        return redirect('user_list')
    suppliers = Supplier.objects.annotate(
        total_pos=Count('purchases'),
        purchased_amount=Sum('purchases__total_amount')
    ).all()
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})


@login_required
def supplier_create(request):
    """Create supplier."""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            s = form.save()
            messages.success(request, f"Supplier '{s.name}' added successfully!")
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'inventory/supplier_form.html', {'form': form, 'title': 'Add Supplier'})


@login_required
def supplier_update(request, pk):
    """Edit supplier."""
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f"Supplier '{supplier.name}' updated successfully!")
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'inventory/supplier_form.html', {'form': form, 'title': f'Edit Supplier: {supplier.name}'})


@login_required
def purchase_list(request):
    """List purchase orders."""
    if request.user.is_superuser:
        return redirect('user_list')
    purchases = Purchase.objects.select_related('supplier').prefetch_related('items').order_by('-purchase_date')
    return render(request, 'inventory/purchase_list.html', {'purchases': purchases})


@login_required
def purchase_create(request):
    """Create a new Purchase Order / Stock In with automatic inventory increment."""
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.can_manage_suppliers)):
        messages.error(request, "Access Restricted: You do not have permission to create purchase orders. Contact the Website Owner.")
        return redirect('purchase_list')

    suppliers = Supplier.objects.all()
    products = Product.objects.filter(is_active=True).order_by('name')

    # Pre-select product if coming from low-stock restock button
    preselect_product_id = request.GET.get('product_id')

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        invoice_number = request.POST.get('invoice_number', '').strip()
        status = request.POST.get('status', 'received')
        notes = request.POST.get('notes', '')

        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')
        unit_costs = request.POST.getlist('unit_cost[]')

        supplier = get_object_or_404(Supplier, id=supplier_id)

        items_data = []
        for pid, qty, cost in zip(product_ids, quantities, unit_costs):
            if pid and qty and cost:
                items_data.append({
                    'product_id': int(pid),
                    'quantity': int(qty),
                    'unit_cost': Decimal(str(cost))
                })

        if not items_data:
            messages.error(request, "Please add at least one product item to the purchase order.")
            return render(request, 'inventory/purchase_form.html', {'suppliers': suppliers, 'products': products, 'preselect_product_id': preselect_product_id})

        try:
            purchase = process_purchase_order(
                supplier=supplier,
                invoice_number=invoice_number,
                items_data=items_data,
                status=status,
                notes=notes
            )
            messages.success(request, f"Purchase Order #{purchase.invoice_number} saved! Inventory automatically updated.")
            return redirect('purchase_detail', pk=purchase.id)
        except Exception as e:
            messages.error(request, f"Error creating purchase order: {str(e)}")

    return render(request, 'inventory/purchase_form.html', {
        'suppliers': suppliers,
        'products': products,
        'preselect_product_id': int(preselect_product_id) if preselect_product_id else None
    })


@login_required
def purchase_detail(request, pk):
    """View purchase order invoice details."""
    purchase = get_object_or_404(Purchase.objects.prefetch_related('items__product', 'supplier'), pk=pk)
    return render(request, 'inventory/purchase_detail.html', {'purchase': purchase})


# ==========================================
# SALES & BILLING RECORDS
# ==========================================
@login_required
def sale_list(request):
    """Sales history list with filtering and search."""
    if request.user.is_superuser:
        return redirect('user_list')
    sales = Sale.objects.prefetch_related('items').order_by('-sale_date')
    
    q = request.GET.get('q', '').strip()
    payment = request.GET.get('payment')
    date_filter = request.GET.get('date')

    if q:
        sales = sales.filter(Q(invoice_number__icontains=q) | Q(customer_name__icontains=q) | Q(customer_phone__icontains=q))

    if payment:
        sales = sales.filter(payment_method=payment)

    if date_filter == 'today':
        sales = sales.filter(sale_date__date=timezone.now().date())
    elif date_filter == 'this_week':
        week_ago = timezone.now().date() - timedelta(days=7)
        sales = sales.filter(sale_date__date__gte=week_ago)
    elif date_filter == 'this_month':
        sales = sales.filter(sale_date__year=timezone.now().year, sale_date__month=timezone.now().month)

    total_sales_sum = sum(s.grand_total for s in sales)
    total_profit_sum = sum(s.total_profit for s in sales)

    context = {
        'sales': sales,
        'total_sales_sum': total_sales_sum,
        'total_profit_sum': total_profit_sum,
        'selected_payment': payment,
        'selected_date': date_filter,
        'q': q,
    }
    return render(request, 'inventory/sale_list.html', context)


@login_required
def sale_detail(request, pk):
    """View and print customer receipt / invoice."""
    sale = get_object_or_404(Sale.objects.prefetch_related('items__product'), pk=pk)
    return render(request, 'inventory/sale_receipt.html', {'sale': sale})


# ==========================================
# STOCK ADJUSTMENTS & AUDIT TRAIL
# ==========================================
@login_required
def stock_adjustment_list(request):
    """Stock movement audit logs and adjustment form."""
    if request.user.is_superuser:
        return redirect('user_list')
    movements = StockMovement.objects.select_related('product').order_by('-created_at')[:100]
    can_adjust = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.can_adjust_stock)

    if request.method == 'POST':
        if not can_adjust:
            messages.error(request, "Access Restricted: You do not have permission to make stock adjustments. Contact the Website Owner.")
            return redirect('stock_adjustment_list')

        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            movement_type = form.cleaned_data['movement_type']
            quantity_change = form.cleaned_data['quantity_change']
            ref = form.cleaned_data['reference_number']
            notes = form.cleaned_data['notes']

            try:
                manual_stock_adjustment(
                    product=product,
                    quantity_change=quantity_change,
                    movement_type=movement_type,
                    reference=ref,
                    notes=notes
                )
                messages.success(request, f"Stock for '{product.name}' adjusted by {quantity_change:+d}. New stock: {product.current_stock}")
                return redirect('stock_adjustment_list')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = StockAdjustmentForm()

    return render(request, 'inventory/stock_adjustments.html', {'movements': movements, 'form': form})


# ==========================================
# PROFIT & INVENTORY REPORTS
# ==========================================
@login_required
def reports_view(request):
    """Comprehensive Profit, Loss, and Inventory Valuation Reports."""
    if request.user.is_superuser:
        return redirect('user_list')
    if not (hasattr(request.user, 'profile') and request.user.profile.can_view_reports):
        messages.error(request, "Access Restricted: You do not have permission to view Financial & Profit reports. Contact the Website Owner.")
        return redirect('dashboard')

    range_type = request.GET.get('range', 'this_month')
    now = timezone.now()
    today = now.date()

    if range_type == 'today':
        start_date = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        end_date = now
    elif range_type == 'last_7_days':
        start_date = timezone.make_aware(timezone.datetime.combine(today - timedelta(days=7), timezone.datetime.min.time()))
        end_date = now
    elif range_type == 'this_month':
        start_date = timezone.make_aware(timezone.datetime(today.year, today.month, 1))
        end_date = now
    elif range_type == 'last_30_days':
        start_date = timezone.make_aware(timezone.datetime.combine(today - timedelta(days=30), timezone.datetime.min.time()))
        end_date = now
    elif range_type == 'this_year':
        start_date = timezone.make_aware(timezone.datetime(today.year, 1, 1))
        end_date = now
    else: # all time
        start_date = timezone.make_aware(timezone.datetime(2000, 1, 1))
        end_date = now

    sales = Sale.objects.filter(status='completed', sale_date__range=(start_date, end_date)).prefetch_related('items')

    # Aggregates
    total_revenue = Decimal('0.00')
    total_cogs = Decimal('0.00')
    total_tax = Decimal('0.00')
    total_discount = Decimal('0.00')
    total_units_sold = 0

    for s in sales:
        total_revenue += s.grand_total
        total_tax += s.tax_amount
        total_discount += s.discount_amount
        for item in s.items.all():
            total_cogs += (item.cost_price * item.quantity)
            total_units_sold += item.quantity

    gross_profit = (total_revenue - total_tax) - total_cogs
    profit_margin = round((gross_profit / (total_revenue - total_tax)) * Decimal('100'), 1) if (total_revenue - total_tax) > 0 else Decimal('0.0')

    # Top selling products in this range
    top_items = (
        SaleItem.objects.filter(sale__status='completed', sale__sale_date__range=(start_date, end_date))
        .values('product__id', 'product__name', 'product__sku')
        .annotate(
            units_sold=Sum('quantity'),
            total_sales_value=Sum('total_price'),
            total_item_cogs=Sum(F('cost_price') * F('quantity'))
        )
        .order_by('-units_sold')[:10]
    )

    top_products_list = []
    for item in top_items:
        revenue = item['total_sales_value'] or Decimal('0.00')
        cogs = item['total_item_cogs'] or Decimal('0.00')
        item_profit = revenue - cogs
        margin = round((item_profit / revenue) * Decimal('100'), 1) if revenue > 0 else Decimal('0')
        top_products_list.append({
            'name': item['product__name'],
            'sku': item['product__sku'],
            'units_sold': item['units_sold'],
            'revenue': revenue,
            'cogs': cogs,
            'profit': item_profit,
            'margin': margin,
        })

    # Inventory Valuation
    all_products = Product.objects.all()
    inventory_valuation_cost = sum(p.inventory_value_cost for p in all_products)
    inventory_valuation_retail = sum(p.inventory_value_retail for p in all_products)
    potential_future_profit = inventory_valuation_retail - inventory_valuation_cost
    total_items_in_stock = sum(max(0, p.current_stock) for p in all_products)

    # Category breakdown
    category_sales = (
        SaleItem.objects.filter(sale__status='completed', sale__sale_date__range=(start_date, end_date))
        .values('product__category__name')
        .annotate(total_revenue=Sum('total_price'), total_qty=Sum('quantity'))
        .order_by('-total_revenue')
    )

    # Payment Methods breakdown
    payment_breakdown = (
        sales.values('payment_method')
        .annotate(total_amt=Sum('grand_total'), count=Count('id'))
        .order_by('-total_amt')
    )

    context = {
        'range_type': range_type,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales_count': sales.count(),
        'total_revenue': total_revenue,
        'total_cogs': total_cogs,
        'total_tax': total_tax,
        'total_discount': total_discount,
        'gross_profit': gross_profit,
        'profit_margin': profit_margin,
        'total_units_sold': total_units_sold,
        'top_products': top_products_list,
        'inventory_valuation_cost': inventory_valuation_cost,
        'inventory_valuation_retail': inventory_valuation_retail,
        'potential_future_profit': potential_future_profit,
        'total_items_in_stock': total_items_in_stock,
        'category_sales': category_sales,
        'payment_breakdown': payment_breakdown,
    }
    return render(request, 'inventory/reports.html', context)


# ==========================================
# SUPER ADMIN (WEBSITE OWNER): USER MANAGEMENT & ACCESS CONTROL
# ==========================================
@superuser_required
def user_list(request):
    """Website Owner portal listing all system users with role, status, and granular permissions."""
    users = User.objects.all().select_related('profile', 'profile__assigned_store').order_by('-date_joined')
    
    user_data = []
    for u in users:
        profile = getattr(u, 'profile', None)
        if not profile:
            profile, _ = UserProfile.objects.get_or_create(
                user=u,
                defaults={
                    'role_title': "Website Owner" if u.is_superuser else ("Store Manager" if u.is_staff else "Cashier"),
                    'can_access_pos': True,
                    'can_manage_products': u.is_staff or u.is_superuser,
                    'can_manage_suppliers': u.is_staff or u.is_superuser,
                    'can_view_reports': u.is_staff or u.is_superuser,
                    'can_adjust_stock': u.is_staff or u.is_superuser,
                }
            )

        if u.is_superuser:
            role = 'Website Owner (Super Admin)'
            role_badge = 'bg-danger'
        elif profile.can_manage_stores:
            role = 'Store Admin (Multi-Store)'
            role_badge = 'bg-warning text-dark'
        elif u.is_staff:
            role = profile.role_title or 'Store Manager'
            role_badge = 'bg-primary'
        else:
            role = profile.role_title or 'POS Cashier'
            role_badge = 'bg-info text-dark'
            
        user_data.append({
            'user': u,
            'profile': profile,
            'role': role,
            'role_badge': role_badge,
        })

    context = {
        'users_list': user_data,
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
        'inactive_users': users.filter(is_active=False).count(),
    }
    return render(request, 'inventory/user_list.html', context)


@superuser_required
def user_create(request):
    """Website Owner: Add new system user and configure access permissions."""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            if User.objects.filter(username=username).exists():
                form.add_error('username', 'Username already taken.')
            else:
                user = User(
                    username=username,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    email=form.cleaned_data['email'],
                    is_active=form.cleaned_data['is_active']
                )
                user.set_password(form.cleaned_data['password'])
                
                role = form.cleaned_data['role']
                if role == 'admin':
                    user.is_superuser = True
                    user.is_staff = True
                    role_title = "Website Owner"
                elif role == 'store_admin':
                    user.is_superuser = False
                    user.is_staff = True
                    role_title = "Store Admin"
                elif role == 'manager':
                    user.is_superuser = False
                    user.is_staff = True
                    role_title = "Store Manager"
                else:
                    user.is_superuser = False
                    user.is_staff = False
                    role_title = "POS Cashier"

                user.save()

                # Configure UserProfile access permissions
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.role_title = role_title
                profile.assigned_store = form.cleaned_data.get('assigned_store')
                profile.can_manage_stores = form.cleaned_data.get('can_manage_stores', False) or (role == 'store_admin') or user.is_superuser
                profile.can_access_pos = form.cleaned_data['can_access_pos']
                profile.can_manage_products = form.cleaned_data['can_manage_products'] if not user.is_superuser else True
                profile.can_manage_suppliers = form.cleaned_data['can_manage_suppliers'] if not user.is_superuser else True
                profile.can_view_reports = form.cleaned_data['can_view_reports'] if not user.is_superuser else True
                profile.can_adjust_stock = form.cleaned_data['can_adjust_stock'] if not user.is_superuser else True
                profile.save()

                messages.success(request, f"User account '{user.username}' created and access permissions configured!")
                return redirect('user_list')
    else:
        form = UserCreateForm()

    return render(request, 'inventory/user_form.html', {'form': form, 'title': 'Create New User & Configure Access'})


@superuser_required
def user_update(request, pk):
    """Website Owner: Modify user details, roles, and access permissions."""
    target_user = get_object_or_404(User.objects.select_related('profile'), pk=pk)
    profile, _ = UserProfile.objects.get_or_create(
        user=target_user,
        defaults={
            'role_title': "Website Owner" if target_user.is_superuser else ("Store Manager" if target_user.is_staff else "Cashier"),
            'can_access_pos': True,
            'can_manage_products': target_user.is_staff or target_user.is_superuser,
            'can_manage_suppliers': target_user.is_staff or target_user.is_superuser,
            'can_view_reports': target_user.is_staff or target_user.is_superuser,
            'can_adjust_stock': target_user.is_staff or target_user.is_superuser,
        }
    )

    if request.method == 'POST':
        form = UserEditForm(request.POST)
        if form.is_valid():
            target_user.first_name = form.cleaned_data['first_name']
            target_user.last_name = form.cleaned_data['last_name']
            target_user.email = form.cleaned_data['email']
            
            # Prevent superuser from deactivating themselves
            if target_user == request.user and not form.cleaned_data['is_active']:
                messages.error(request, "Security: You cannot deactivate your own Website Owner account!")
                return redirect('user_list')

            target_user.is_active = form.cleaned_data['is_active']

            role = form.cleaned_data['role']
            if role == 'admin':
                target_user.is_superuser = True
                target_user.is_staff = True
                role_title = "Website Owner"
            elif role == 'store_admin':
                target_user.is_superuser = False
                target_user.is_staff = True
                role_title = "Store Admin"
            elif role == 'manager':
                target_user.is_superuser = False
                target_user.is_staff = True
                role_title = "Store Manager"
            else:
                if target_user == request.user:
                    messages.error(request, "Security: You cannot revoke your own Website Owner privileges!")
                    return redirect('user_list')
                target_user.is_superuser = False
                target_user.is_staff = False
                role_title = "POS Cashier"

            new_pass = form.cleaned_data.get('new_password')
            if new_pass:
                target_user.set_password(new_pass)
                messages.info(request, f"Password for '{target_user.username}' has been updated.")

            target_user.save()

            # Update Access Permissions in UserProfile
            profile.role_title = role_title
            profile.assigned_store = form.cleaned_data.get('assigned_store')
            profile.can_manage_stores = form.cleaned_data.get('can_manage_stores', False) or (role == 'store_admin') or target_user.is_superuser
            profile.can_access_pos = form.cleaned_data['can_access_pos']
            profile.can_manage_products = form.cleaned_data['can_manage_products'] if not target_user.is_superuser else True
            profile.can_manage_suppliers = form.cleaned_data['can_manage_suppliers'] if not target_user.is_superuser else True
            profile.can_view_reports = form.cleaned_data['can_view_reports'] if not target_user.is_superuser else True
            profile.can_adjust_stock = form.cleaned_data['can_adjust_stock'] if not target_user.is_superuser else True
            profile.save()

            messages.success(request, f"Access privileges and details for '{target_user.username}' updated successfully!")
            return redirect('user_list')
    else:
        if target_user.is_superuser:
            current_role = 'admin'
        elif profile.can_manage_stores:
            current_role = 'store_admin'
        elif target_user.is_staff:
            current_role = 'manager'
        else:
            current_role = 'cashier'

        initial_data = {
            'first_name': target_user.first_name,
            'last_name': target_user.last_name,
            'email': target_user.email,
            'is_active': target_user.is_active,
            'role': current_role,
            'assigned_store': profile.assigned_store,
            'can_manage_stores': profile.can_manage_stores,
            'can_access_pos': profile.can_access_pos,
            'can_manage_products': profile.can_manage_products,
            'can_manage_suppliers': profile.can_manage_suppliers,
            'can_view_reports': profile.can_view_reports,
            'can_adjust_stock': profile.can_adjust_stock,
        }
        form = UserEditForm(initial=initial_data)

    return render(request, 'inventory/user_form.html', {
        'form': form, 
        'title': f'Manage Access & Details: {target_user.username}',
        'target_user': target_user
    })


@superuser_required
def user_delete(request, pk):
    """Super Admin: Delete user account."""
    target_user = get_object_or_404(User, pk=pk)

    if target_user == request.user:
        messages.error(request, "Security protection: You cannot delete your own Super Admin account!")
        return redirect('user_list')

    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f"User account '{username}' was permanently deleted.")
        return redirect('user_list')

    return render(request, 'inventory/confirm_delete.html', {
        'object': f"User account '{target_user.username}' ({target_user.get_full_name() or 'No name'})",
        'type': 'User Account'
    })


@superuser_required
def user_toggle_status(request, pk):
    """Super Admin: 1-click toggle user active/inactive."""
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('user_list')

    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=['is_active'])
    status_label = "activated" if target_user.is_active else "deactivated"
    messages.success(request, f"User '{target_user.username}' has been {status_label}.")
    return redirect('user_list')


# ==========================================
# STORE & BRANCH MANAGEMENT (STORE ADMIN / OWNER)
# ==========================================
@store_admin_required
def store_list(request):
    """Store Admin page listing all business store branches & performance."""
    stores = Store.objects.prefetch_related('staff_members', 'sales').all()
    context = {
        'stores': stores,
        'total_stores': stores.count(),
        'active_stores': stores.filter(is_active=True).count(),
        'inactive_stores': stores.filter(is_active=False).count(),
    }
    return render(request, 'inventory/store_list.html', context)


@store_admin_required
def store_create(request):
    """Store Admin: Add new store branch / outlet."""
    if request.method == 'POST':
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save()
            messages.success(request, f"New store branch '{store.name}' ({store.code}) added successfully!")
            return redirect('store_list')
    else:
        form = StoreForm()

    return render(request, 'inventory/store_form.html', {'form': form, 'title': 'Add New Store Branch / Outlet'})


@store_admin_required
def store_update(request, pk):
    """Store Admin: Edit / modify store location, manager, and operational status."""
    store = get_object_or_404(Store, pk=pk)
    if request.method == 'POST':
        form = StoreForm(request.POST, instance=store)
        if form.is_valid():
            store = form.save()
            messages.success(request, f"Store branch '{store.name}' updated successfully!")
            return redirect('store_list')
    else:
        form = StoreForm(instance=store)

    return render(request, 'inventory/store_form.html', {'form': form, 'title': f'Modify Store: {store.name}', 'store': store})


@store_admin_required
def store_toggle_status(request, pk):
    """Store Admin: 1-click toggle store operational status."""
    store = get_object_or_404(Store, pk=pk)
    if store.is_main and store.is_active:
        messages.warning(request, "Primary flagship store should remain active.")
        return redirect('store_list')

    store.is_active = not store.is_active
    store.save(update_fields=['is_active'])
    status_label = "opened/activated" if store.is_active else "closed/deactivated"
    messages.success(request, f"Store '{store.name}' is now {status_label}.")
    return redirect('store_list')


@store_admin_required
def store_delete(request, pk):
    """Store Admin: Delete store branch."""
    store = get_object_or_404(Store, pk=pk)
    if store.is_main:
        messages.error(request, "Primary flagship store cannot be deleted.")
        return redirect('store_list')

    if request.method == 'POST':
        name = store.name
        store.delete()
        messages.success(request, f"Store outlet '{name}' was deleted.")
        return redirect('store_list')

    return render(request, 'inventory/confirm_delete.html', {
        'object': f"Store Branch '{store.name}' ({store.code})",
        'type': 'Store Branch'
    })


