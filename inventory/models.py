from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def product_count(self):
        return self.products.count()


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30)
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def total_purchases_amount(self):
        return sum(p.total_amount for p in self.purchases.filter(status='received'))


class Product(models.Model):
    UNIT_CHOICES = [
        ('pcs', 'Pieces (pcs)'),
        ('box', 'Box'),
        ('kg', 'Kilogram (kg)'),
        ('g', 'Gram (g)'),
        ('ltr', 'Liter (ltr)'),
        ('pack', 'Pack'),
        ('carton', 'Carton'),
    ]

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit / Code")
    barcode = models.CharField(max_length=64, blank=True, null=True, unique=True, help_text="Barcode / EAN / UPC")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Cost / Purchase price")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Retail / Selling price")
    current_stock = models.IntegerField(default=0, help_text="Current units in inventory")
    min_stock_level = models.IntegerField(default=10, help_text="Threshold for low-stock alert")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='pcs')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_low_stock(self):
        """Check if stock is at or below minimum threshold."""
        return 0 < self.current_stock <= self.min_stock_level

    @property
    def is_out_of_stock(self):
        """Check if completely out of stock."""
        return self.current_stock <= 0

    @property
    def stock_status(self):
        if self.current_stock <= 0:
            return 'out_of_stock'
        elif self.current_stock <= self.min_stock_level:
            return 'low_stock'
        return 'in_stock'

    @property
    def profit_per_unit(self):
        return self.selling_price - self.cost_price

    @property
    def margin_percentage(self):
        if self.selling_price > Decimal('0'):
            margin = ((self.selling_price - self.cost_price) / self.selling_price) * Decimal('100')
            return round(margin, 1)
        return Decimal('0')

    @property
    def inventory_value_cost(self):
        return max(0, self.current_stock) * self.cost_price

    @property
    def inventory_value_retail(self):
        return max(0, self.current_stock) * self.selling_price


class Customer(models.Model):
    name = models.CharField(max_length=150, default='Walk-in Customer')
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone or 'No Phone'})"


class Purchase(models.Model):
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('pending', 'Pending Order'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=60, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchases')
    purchase_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-purchase_date']

    def __str__(self):
        return f"PO #{self.invoice_number} - {self.supplier.name}"

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='purchase_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Sale(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit / Debit Card'),
        ('upi', 'UPI / QR Code'),
        ('transfer', 'Bank Transfer'),
        ('due', 'Credit / Due'),
    ]

    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=60, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    customer_name = models.CharField(max_length=150, default='Walk-in Customer')
    customer_phone = models.CharField(max_length=30, blank=True, null=True)
    sale_date = models.DateTimeField(default=timezone.now)
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Tax percentage e.g. 5.00 for 5%")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    cashier = models.CharField(max_length=100, default='Cashier 1')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sale_date']

    def __str__(self):
        return f"Invoice #{self.invoice_number} - ${self.grand_total}"

    @property
    def total_cost(self):
        """Total cost of goods sold (COGS) for this sale."""
        return sum(item.cost_price * item.quantity for item in self.items.all())

    @property
    def total_profit(self):
        """Gross profit for this sale (Subtotal - Discount - COGS)."""
        net_revenue = self.subtotal - self.discount_amount
        return net_revenue - self.total_cost

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_items')
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2) # selling price per item
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # recorded cost at time of sale
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    @property
    def item_profit(self):
        revenue = self.total_price
        cogs = self.cost_price * self.quantity
        return revenue - cogs


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('purchase', 'Purchase / Stock In'),
        ('sale', 'POS Sale / Stock Out'),
        ('adjustment', 'Manual Adjustment'),
        ('damage', 'Damaged / Expired'),
        ('return', 'Customer Return'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField(help_text="Positive for addition, negative for deduction")
    previous_stock = models.IntegerField()
    new_stock = models.IntegerField()
    reference_number = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Invoice # or PO #")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} ({self.quantity:+d}) - {self.movement_type}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role_title = models.CharField(max_length=100, default='Cashier')
    phone = models.CharField(max_length=30, blank=True, null=True)
    can_access_pos = models.BooleanField(default=True, verbose_name="Access POS Billing", help_text="Can create bills and process sales at POS terminal")
    can_manage_products = models.BooleanField(default=False, verbose_name="Manage Inventory Products", help_text="Can add, edit, or delete catalog products")
    can_manage_suppliers = models.BooleanField(default=False, verbose_name="Manage Suppliers & POs", help_text="Can add suppliers and create purchase orders")
    can_view_reports = models.BooleanField(default=False, verbose_name="View Financial & Profit Reports", help_text="Can view gross profit, revenue, and margins")
    can_adjust_stock = models.BooleanField(default=False, verbose_name="Perform Stock Adjustments", help_text="Can manually adjust stock and log audit movements")
    notes = models.TextField(blank=True, null=True, help_text="Owner's internal notes on this user")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.role_title})"

    @property
    def is_owner(self):
        return self.user.is_superuser


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        role = "Website Owner" if instance.is_superuser else ("Store Manager" if instance.is_staff else "Cashier")
        UserProfile.objects.create(
            user=instance,
            role_title=role,
            can_access_pos=True,
            can_manage_products=instance.is_staff or instance.is_superuser,
            can_manage_suppliers=instance.is_staff or instance.is_superuser,
            can_view_reports=instance.is_staff or instance.is_superuser,
            can_adjust_stock=instance.is_staff or instance.is_superuser,
        )

