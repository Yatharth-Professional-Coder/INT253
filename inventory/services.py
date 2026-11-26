import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Product, Sale, SaleItem, Purchase, PurchaseItem, StockMovement, Customer

def generate_invoice_number(prefix="INV"):
    today_str = timezone.now().strftime("%Y%m%d")
    random_suffix = uuid.uuid4().hex[:5].upper()
    return f"{prefix}-{today_str}-{random_suffix}"

def generate_po_number():
    return generate_invoice_number(prefix="PO")

@transaction.atomic
def process_pos_sale(items, customer=None, customer_name="Walk-in Customer", customer_phone="",
                     tax_rate=Decimal('0.0'), discount_amount=Decimal('0.0'),
                     amount_paid=Decimal('0.0'), payment_method="cash", cashier="Cashier", notes=""):
    """
    Process a POS sale with automatic inventory deduction and stock movement audit log.
    items: list of dicts: [{'product_id': int, 'quantity': int, 'unit_price': Decimal, 'discount': Decimal}]
    """
    if not items:
        raise ValueError("Cannot process empty sale.")

    # 1. Validate items and stock
    validated_items = []
    subtotal = Decimal('0.00')

    for item_data in items:
        product = Product.objects.select_for_update().get(id=item_data['product_id'])
        qty = int(item_data['quantity'])
        if qty <= 0:
            raise ValueError(f"Invalid quantity for {product.name}")
        
        if product.current_stock < qty:
            raise ValueError(f"Insufficient stock for {product.name}. Available: {product.current_stock}, Requested: {qty}")

        unit_price = Decimal(str(item_data.get('unit_price', product.selling_price)))
        discount = Decimal(str(item_data.get('discount', 0)))
        line_total = (unit_price * qty) - discount
        subtotal += line_total

        validated_items.append({
            'product': product,
            'quantity': qty,
            'unit_price': unit_price,
            'cost_price': product.cost_price,
            'discount': discount,
            'line_total': line_total
        })

    # 2. Compute financial totals
    tax_rate = Decimal(str(tax_rate))
    discount_amount = Decimal(str(discount_amount))
    taxable_amount = max(Decimal('0.00'), subtotal - discount_amount)
    tax_amount = round(taxable_amount * (tax_rate / Decimal('100')), 2)
    grand_total = taxable_amount + tax_amount

    if payment_method in ['card', 'upi']:
        amount_paid = grand_total
        change_amount = Decimal('0.00')
    elif payment_method == 'due':
        amount_paid = Decimal('0.00')
        change_amount = Decimal('0.00')
    else:
        amount_paid = Decimal(str(amount_paid)) if amount_paid else grand_total
        change_amount = max(Decimal('0.00'), amount_paid - grand_total)

    invoice_no = generate_invoice_number("INV")

    # 3. Create Sale
    sale = Sale.objects.create(
        invoice_number=invoice_no,
        customer=customer,
        customer_name=customer_name or "Walk-in Customer",
        customer_phone=customer_phone,
        subtotal=subtotal,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        discount_amount=discount_amount,
        grand_total=grand_total,
        amount_paid=amount_paid,
        change_amount=change_amount,
        payment_method=payment_method,
        cashier=cashier,
        notes=notes,
        status='completed'
    )

    # 4. Create SaleItems & update stock automatically
    for item in validated_items:
        product = item['product']
        qty = item['quantity']
        
        SaleItem.objects.create(
            sale=sale,
            product=product,
            product_name=product.name,
            quantity=qty,
            unit_price=item['unit_price'],
            cost_price=item['cost_price'],
            discount_amount=item['discount'],
            total_price=item['line_total']
        )

        prev_stock = product.current_stock
        new_stock = prev_stock - qty
        product.current_stock = new_stock
        product.save(update_fields=['current_stock', 'updated_at'])

        StockMovement.objects.create(
            product=product,
            movement_type='sale',
            quantity=-qty,
            previous_stock=prev_stock,
            new_stock=new_stock,
            reference_number=invoice_no,
            notes=f"POS Sale Invoice #{invoice_no}"
        )

    return sale


@transaction.atomic
def process_purchase_order(supplier, invoice_number, items_data, status='received', purchase_date=None, notes=""):
    """
    Process a supplier purchase order. If status is 'received', automatically updates product stock & cost price.
    items_data: list of dicts [{'product_id': int, 'quantity': int, 'unit_cost': Decimal}]
    """
    if not invoice_number:
        invoice_number = generate_po_number()

    if purchase_date is None:
        purchase_date = timezone.now()

    total_amount = Decimal('0.00')
    validated_items = []

    for item in items_data:
        product = Product.objects.select_for_update().get(id=item['product_id'])
        qty = int(item['quantity'])
        cost = Decimal(str(item['unit_cost']))
        line_total = cost * qty
        total_amount += line_total
        validated_items.append({
            'product': product,
            'quantity': qty,
            'unit_cost': cost,
            'total_price': line_total
        })

    purchase = Purchase.objects.create(
        invoice_number=invoice_number,
        supplier=supplier,
        purchase_date=purchase_date,
        total_amount=total_amount,
        status=status,
        notes=notes
    )

    for item in validated_items:
        product = item['product']
        qty = item['quantity']
        cost = item['unit_cost']

        PurchaseItem.objects.create(
            purchase=purchase,
            product=product,
            quantity=qty,
            unit_cost=cost,
            total_price=item['total_price']
        )

        # Automatic Stock Update when Received
        if status == 'received':
            prev_stock = product.current_stock
            new_stock = prev_stock + qty
            product.current_stock = new_stock
            product.cost_price = cost # update latest purchase cost
            product.save(update_fields=['current_stock', 'cost_price', 'updated_at'])

            StockMovement.objects.create(
                product=product,
                movement_type='purchase',
                quantity=qty,
                previous_stock=prev_stock,
                new_stock=new_stock,
                reference_number=invoice_number,
                notes=f"Purchase Order #{invoice_number} from {supplier.name}"
            )

    return purchase


@transaction.atomic
def manual_stock_adjustment(product, quantity_change, movement_type='adjustment', reference="", notes=""):
    """
    Manually adjust stock for audits, damage, or corrections.
    """
    product = Product.objects.select_for_update().get(id=product.id)
    prev_stock = product.current_stock
    new_stock = prev_stock + quantity_change
    if new_stock < 0:
        raise ValueError("Stock cannot be negative after adjustment.")

    product.current_stock = new_stock
    product.save(update_fields=['current_stock', 'updated_at'])

    StockMovement.objects.create(
        product=product,
        movement_type=movement_type,
        quantity=quantity_change,
        previous_stock=prev_stock,
        new_stock=new_stock,
        reference_number=reference,
        notes=notes
    )

    return product

