import random
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from inventory.models import Category, Supplier, Product, Customer, Purchase, PurchaseItem, Sale, SaleItem, StockMovement, Store, UserProfile

class Command(BaseCommand):
    help = 'Seed realistic sample inventory, suppliers, purchases, sales, and low-stock alerts'

    def handle(self, *args, **options):
        self.stdout.write("Seeding database with sample inventory data...")

        # Clear existing non-admin data
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

        # 0. Create Retail Store Branches
        store_hq = Store.objects.create(
            name="SmartStock Flagship (Downtown)",
            code="STR-01",
            manager_name="Marcus Sterling",
            city="San Jose, CA",
            phone="+1 (555) 100-2001",
            email="downtown@smartstock.local",
            address="100 Grand Boulevard, Downtown",
            is_main=True,
            is_active=True
        )
        store_mall = Store.objects.create(
            name="SmartStock Metro Mall Branch",
            code="STR-02",
            manager_name="Jessica Taylor",
            city="San Francisco, CA",
            phone="+1 (555) 100-2002",
            email="metromall@smartstock.local",
            address="Level 2, North Wing, Metro Mall",
            is_main=False,
            is_active=True
        )
        store_west = Store.objects.create(
            name="SmartStock Westside Express",
            code="STR-03",
            manager_name="David Kim",
            city="Oakland, CA",
            phone="+1 (555) 100-2003",
            email="westside@smartstock.local",
            address="742 Sunset Avenue",
            is_main=False,
            is_active=True
        )
        all_stores = [store_hq, store_mall, store_west]

        # 1. Create Categories
        categories_data = [
            ("Electronics & Gadgets", "Laptops, audio, accessories, and cables"),
            ("Office & Stationery", "Paper, pens, desk organizers, and notebooks"),
            ("Food & Beverages", "Snacks, coffee, tea, and packaged beverages"),
            ("Health & Personal Care", "Sanitizers, masks, skincare, and hygiene"),
            ("Home & Hardware", "Batteries, tools, lighting, and home accessories"),
        ]
        cat_objs = {}
        for name, desc in categories_data:
            cat_objs[name] = Category.objects.create(name=name, description=desc)

        # 2. Create Suppliers
        suppliers_data = [
            ("TechWorld Distributors", "Alex Rivera", "+1 (555) 234-5678", "alex@techworld.io", "120 Silicon Way, San Jose, CA"),
            ("Apex Office Direct", "Melissa Chang", "+1 (555) 876-5432", "orders@apexoffice.com", "450 Industrial Blvd, Chicago, IL"),
            ("GreenValley Provisions", "Robert Davies", "+1 (555) 345-6789", "robert@greenvalley.com", "88 Orchard Road, Portland, OR"),
            ("VitalCare Supply Co.", "Dr. Elena Ramos", "+1 (555) 901-2345", "supply@vitalcare.net", "720 Medical Plaza, Dallas, TX"),
        ]
        sup_objs = {}
        for name, contact, phone, email, addr in suppliers_data:
            sup_objs[name] = Supplier.objects.create(
                name=name, contact_name=contact, phone=phone, email=email, address=addr
            )

        # 3. Create Customers
        customers_data = [
            ("Walk-in Customer", "", "walkin@store.local"),
            ("Marcus Sterling", "+1 (555) 111-2233", "marcus.s@gmail.com"),
            ("Jessica Taylor", "+1 (555) 222-3344", "jess.taylor@outlook.com"),
            ("David Kim", "+1 (555) 333-4455", "dkim_creative@yahoo.com"),
            ("Olivia Martinez", "+1 (555) 444-5566", "olivia.m@company.org"),
        ]
        cust_objs = []
        for name, phone, email in customers_data:
            c = Customer.objects.create(name=name, phone=phone, email=email)
            cust_objs.append(c)

        # 4. Create Products (Normal, Low Stock, and Out of Stock for Alert Demonstration)
        products_data = [
            # Electronics
            ("Logitech MX Master 3S Mouse", "ELEC-LOG-01", "8901001", "Electronics & Gadgets", "TechWorld Distributors", "62.00", "99.99", 25, 8, "pcs"),
            ("USB-C Fast Charging Cable (2m)", "ELEC-CAB-02", "8901002", "Electronics & Gadgets", "TechWorld Distributors", "4.50", "14.99", 65, 15, "pcs"),
            ("Anker 65W GaN Charger", "ELEC-ANK-03", "8901003", "Electronics & Gadgets", "TechWorld Distributors", "22.00", "45.00", 4, 10, "pcs"), # LOW STOCK!
            ("Sony WH-1000XM5 Headphones", "ELEC-SNY-04", "8901004", "Electronics & Gadgets", "TechWorld Distributors", "240.00", "399.00", 8, 5, "pcs"),
            ("Wireless Mechanical Keyboard RGB", "ELEC-KEY-05", "8901005", "Electronics & Gadgets", "TechWorld Distributors", "48.00", "89.00", 0, 5, "pcs"), # OUT OF STOCK!
            ("SanDisk 128GB Flash Drive 3.1", "ELEC-SAN-06", "8901006", "Electronics & Gadgets", "TechWorld Distributors", "8.00", "18.50", 42, 10, "pcs"),
            
            # Office
            ("Moleskine Classic Hardcover Notebook", "OFF-MOL-01", "8902001", "Office & Stationery", "Apex Office Direct", "11.00", "22.50", 35, 10, "pcs"),
            ("Pilot G2 Gel Pens (Pack of 12)", "OFF-PIL-02", "8902002", "Office & Stationery", "Apex Office Direct", "6.20", "13.99", 5, 12, "pack"), # LOW STOCK!
            ("Multipurpose A4 Copy Paper 500 Sheets", "OFF-PAP-03", "8902003", "Office & Stationery", "Apex Office Direct", "3.80", "7.50", 90, 20, "pack"),
            ("Heavy Duty Metal Stapler", "OFF-STP-04", "8902004", "Office & Stationery", "Apex Office Direct", "5.50", "12.00", 2, 8, "pcs"), # LOW STOCK!
            ("Post-it Super Sticky Notes 6-Pack", "OFF-NOT-05", "8902005", "Office & Stationery", "Apex Office Direct", "4.00", "8.99", 40, 10, "pack"),

            # Food & Beverages
            ("Organic Arabica Whole Bean Coffee 1kg", "F&B-COF-01", "8903001", "Food & Beverages", "GreenValley Provisions", "12.00", "24.00", 18, 10, "kg"),
            ("Matcha Green Tea Powder 100g", "F&B-MTC-02", "8903002", "Food & Beverages", "GreenValley Provisions", "9.50", "19.99", 3, 10, "box"), # LOW STOCK!
            ("Artisan Dark Chocolate Bar 85%", "F&B-CHO-03", "8903003", "Food & Beverages", "GreenValley Provisions", "2.10", "4.99", 50, 15, "pcs"),
            ("Sparkling Mineral Water 750ml", "F&B-WTR-04", "8903004", "Food & Beverages", "GreenValley Provisions", "0.90", "2.49", 120, 24, "pcs"),
            ("Almond Granola Energy Bites 250g", "F&B-GRA-05", "8903005", "Food & Beverages", "GreenValley Provisions", "3.20", "6.99", 0, 8, "pack"), # OUT OF STOCK!

            # Health & Care
            ("Advanced Hand Sanitizer Gel 500ml", "HLT-SAN-01", "8904001", "Health & Personal Care", "VitalCare Supply Co.", "2.40", "5.99", 45, 12, "pcs"),
            ("N95 Protective Face Masks (Box of 20)", "HLT-MSK-02", "8904002", "Health & Personal Care", "VitalCare Supply Co.", "7.00", "15.00", 6, 15, "box"), # LOW STOCK!
            ("Hydrating Daily Sunscreen SPF 50+", "HLT-SUN-03", "8904003", "Health & Personal Care", "VitalCare Supply Co.", "8.50", "18.00", 28, 8, "pcs"),
            
            # Home & Hardware
            ("Energizer AA Alkaline Batteries 16-Pack", "HOM-BAT-01", "8905001", "Home & Hardware", "Apex Office Direct", "6.50", "14.49", 55, 15, "pack"),
            ("Philips Smart LED Bulb 9W (Warm White)", "HOM-LED-02", "8905002", "Home & Hardware", "TechWorld Distributors", "5.00", "12.99", 30, 10, "pcs"),
        ]

        created_products = []
        for name, sku, barcode, cat_name, sup_name, cost, sell, stock, min_stk, unit in products_data:
            p = Product.objects.create(
                name=name,
                sku=sku,
                barcode=barcode,
                category=cat_objs[cat_name],
                supplier=sup_objs[sup_name],
                cost_price=Decimal(cost),
                selling_price=Decimal(sell),
                current_stock=stock,
                min_stock_level=min_stk,
                unit=unit,
                description=f"Standard high quality {name}"
            )
            created_products.append(p)

            # Record initial stock movement
            if stock > 0:
                StockMovement.objects.create(
                    product=p,
                    movement_type='purchase',
                    quantity=stock,
                    previous_stock=0,
                    new_stock=stock,
                    reference_number="PO-INITIAL",
                    notes="Initial inventory setup"
                )

        self.stdout.write(f"Created {len(created_products)} products.")

        # 5. Create Sample Purchases (Stock In)
        suppliers_list = list(sup_objs.values())
        for idx in range(1, 5):
            sup = suppliers_list[idx - 1]
            p_date = timezone.now() - timedelta(days=idx * 4)
            po = Purchase.objects.create(
                invoice_number=f"PO-2026-00{idx}",
                supplier=sup,
                store=random.choice(all_stores),
                purchase_date=p_date,
                status='received',
                notes="Standard monthly restocking inventory order"
            )
            po_total = Decimal('0.00')
            # Select 3-4 products
            sampled_products = random.sample(created_products, 4)
            for prod in sampled_products:
                qty = random.randint(10, 30)
                cost = prod.cost_price
                tot = cost * qty
                po_total += tot
                PurchaseItem.objects.create(
                    purchase=po,
                    product=prod,
                    quantity=qty,
                    unit_cost=cost,
                    total_price=tot
                )
            po.total_amount = po_total
            po.save()

        # 6. Create Historical Sales over the last 14 days
        now = timezone.now()
        payment_methods = ['cash', 'card', 'upi', 'cash', 'card']
        sale_counter = 100

        for days_ago in range(13, -1, -1):
            day_dt = now - timedelta(days=days_ago)
            # Create 2 to 5 sales per day
            num_sales = random.randint(2, 5)
            for _ in range(num_sales):
                sale_counter += 1
                cust = random.choice(cust_objs)
                sale_time = day_dt.replace(hour=random.randint(9, 20), minute=random.randint(0, 59))
                
                # Pick 1 to 4 items
                selected_prods = random.sample(created_products, random.randint(1, 4))
                subtotal = Decimal('0.00')
                items_to_create = []

                for prod in selected_prods:
                    qty = random.randint(1, 3)
                    price = prod.selling_price
                    line_tot = price * qty
                    subtotal += line_tot
                    items_to_create.append((prod, qty, price, prod.cost_price, line_tot))

                tax_rate = Decimal('5.00')
                tax_amt = round(subtotal * Decimal('0.05'), 2)
                discount = Decimal('0.00') if random.random() > 0.3 else Decimal(str(random.randint(1, 5)))
                grand_total = subtotal - discount + tax_amt
                paid = grand_total if random.random() > 0.4 else grand_total + Decimal('10.00')
                change = max(Decimal('0.00'), paid - grand_total)

                sale = Sale.objects.create(
                    invoice_number=f"INV-202611-{sale_counter:04d}",
                    store=random.choice(all_stores),
                    customer=cust if cust.name != "Walk-in Customer" else None,
                    customer_name=cust.name,
                    customer_phone=cust.phone or "",
                    sale_date=sale_time,
                    subtotal=subtotal,
                    tax_rate=tax_rate,
                    tax_amount=tax_amt,
                    discount_amount=discount,
                    grand_total=grand_total,
                    amount_paid=paid,
                    change_amount=change,
                    payment_method=random.choice(payment_methods),
                    cashier=random.choice(["Alex M.", "Sarah K."]),
                    status='completed'
                )

                for prod, qty, price, cost, line_tot in items_to_create:
                    SaleItem.objects.create(
                        sale=sale,
                        product=prod,
                        product_name=prod.name,
                        quantity=qty,
                        unit_price=price,
                        cost_price=cost,
                        discount_amount=Decimal('0.00'),
                        total_price=line_tot
                    )

        # 7. Create Demo Role Accounts
        if not User.objects.filter(username='admin').exists():
            admin_u = User.objects.create_superuser('admin', 'admin@smartstock.local', 'admin123')
            admin_u.first_name = "Alexander"
            admin_u.last_name = "Admin"
            admin_u.save()
        else:
            admin_u = User.objects.get(username='admin')
            admin_u.set_password('admin123')
            admin_u.is_superuser = True
            admin_u.is_staff = True
            admin_u.save()

        # Store Administrator (Can add and modify different stores)
        if not User.objects.filter(username='storeadmin').exists():
            sa_u = User.objects.create_user('storeadmin', 'storeadmin@smartstock.local', 'storeadmin123')
            sa_u.first_name = "Samantha"
            sa_u.last_name = "StoreAdmin"
            sa_u.is_staff = True
            sa_u.save()
        else:
            sa_u = User.objects.get(username='storeadmin')
            sa_u.set_password('storeadmin123')
            sa_u.is_staff = True
            sa_u.is_superuser = False
            sa_u.save()

        sa_profile, _ = UserProfile.objects.get_or_create(user=sa_u)
        sa_profile.role_title = "Store Admin"
        sa_profile.can_manage_stores = True
        sa_profile.can_manage_products = True
        sa_profile.can_manage_suppliers = True
        sa_profile.can_view_reports = True
        sa_profile.can_access_pos = True
        sa_profile.assigned_store = store_hq
        sa_profile.save()

        if not User.objects.filter(username='manager').exists():
            mgr_u = User.objects.create_user('manager', 'manager@smartstock.local', 'manager123')
            mgr_u.first_name = "Marcus"
            mgr_u.last_name = "Manager"
            mgr_u.is_staff = True
            mgr_u.save()
        else:
            mgr_u = User.objects.get(username='manager')
            mgr_u.set_password('manager123')
            mgr_u.is_staff = True
            mgr_u.is_superuser = False
            mgr_u.save()

        if not User.objects.filter(username='cashier1').exists():
            csh_u = User.objects.create_user('cashier1', 'cashier1@smartstock.local', 'cashier123')
            csh_u.first_name = "Chloe"
            csh_u.last_name = "Cashier"
            csh_u.save()
        else:
            csh_u = User.objects.get(username='cashier1')
            csh_u.set_password('cashier123')
            csh_u.is_staff = False
            csh_u.is_superuser = False
            csh_u.save()

        self.stdout.write(self.style.SUCCESS("Successfully seeded comprehensive inventory, suppliers, sales, purchases, and role-based demo accounts!"))

