from django.contrib import admin
from .models import Category, Supplier, Product, Customer, Purchase, PurchaseItem, Sale, SaleItem, StockMovement

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_name', 'phone', 'email')
    search_fields = ('name', 'contact_name', 'phone')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'supplier', 'cost_price', 'selling_price', 'current_stock', 'min_stock_level', 'stock_status')
    list_filter = ('category', 'supplier', 'is_active')
    search_fields = ('name', 'sku', 'barcode')

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'supplier', 'purchase_date', 'total_amount', 'status')
    list_filter = ('status', 'purchase_date')
    search_fields = ('invoice_number', 'supplier__name')
    inlines = [PurchaseItemInline]

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('product_name', 'quantity', 'unit_price', 'cost_price', 'total_price')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer_name', 'sale_date', 'grand_total', 'payment_method', 'status')
    list_filter = ('payment_method', 'status', 'sale_date')
    search_fields = ('invoice_number', 'customer_name', 'customer_phone')
    inlines = [SaleItemInline]

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity', 'previous_stock', 'new_stock', 'reference_number', 'created_at')
    list_filter = ('movement_type', 'created_at')
    search_fields = ('product__name', 'reference_number')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'created_at')
    search_fields = ('name', 'phone', 'email')
