from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import (
    Category, Supplier, Product, Customer, Purchase, PurchaseItem,
    Sale, SaleItem, StockMovement, Store, UserProfile
)

class Command(BaseCommand):
    help = 'Clean all demo data and ensure clean Website Owner (Super Admin) account'

    def handle(self, *args, **options):
        self.stdout.write("Clearing all demo data from database...")

        # Clear existing data
        StockMovement.objects.all().delete()
        SaleItem.objects.all().delete()
        Sale.objects.all().delete()
        PurchaseItem.objects.all().delete()
        Purchase.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Supplier.objects.all().delete()
        Customer.objects.all().delete()
        Store.objects.all().delete()
        User.objects.exclude(username='admin').delete()

        # Ensure clean super admin
        if not User.objects.filter(username='admin').exists():
            admin_u = User.objects.create_superuser('admin', 'admin@smartstock.local', 'admin123')
            admin_u.first_name = "Yatharth"
            admin_u.last_name = ""
            admin_u.save()
        else:
            admin_u = User.objects.get(username='admin')
            admin_u.first_name = "Yatharth"
            admin_u.last_name = ""
            admin_u.set_password('admin123')
            admin_u.is_superuser = True
            admin_u.is_staff = True
            admin_u.save()

        profile, _ = UserProfile.objects.get_or_create(user=admin_u)
        profile.role_title = "Website Owner"
        profile.assigned_store = None
        profile.can_access_pos = False
        profile.can_manage_products = False
        profile.can_manage_suppliers = False
        profile.can_view_reports = False
        profile.can_adjust_stock = False
        profile.can_manage_stores = False
        profile.save()

        self.stdout.write(self.style.SUCCESS("Clean state ready: 0 demo records, Super Admin ready at /login/!"))
