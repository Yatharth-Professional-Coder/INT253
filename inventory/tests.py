from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from inventory.models import Category, Supplier, Product, Customer, Sale, Purchase, StockMovement
from inventory.services import process_pos_sale, process_purchase_order, manual_stock_adjustment

class SmartInventorySystemTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Users
        self.super_admin = User.objects.create_superuser('testadmin', 'admin@test.com', 'pass123')
        self.regular_user = User.objects.create_user('testcashier', 'cashier@test.com', 'pass123')

        # Create Category & Supplier
        self.category = Category.objects.create(name="Tech", description="Electronic gadgets")
        self.supplier = Supplier.objects.create(
            name="Alpha Supplies", contact_name="Rahul Verma", phone="+91 98765 43210", email="rahul@alpha.in"
        )

        # Create Products
        self.prod_normal = Product.objects.create(
            name="Gaming Mouse",
            sku="GM-001",
            barcode="10001",
            category=self.category,
            supplier=self.supplier,
            cost_price=Decimal('20.00'),
            selling_price=Decimal('50.00'),
            current_stock=30,
            min_stock_level=10,
            unit="pcs"
        )

        self.prod_low = Product.objects.create(
            name="Mechanical Keyboard",
            sku="KB-002",
            barcode="10002",
            category=self.category,
            supplier=self.supplier,
            cost_price=Decimal('40.00'),
            selling_price=Decimal('80.00'),
            current_stock=5, # <= min_stock_level
            min_stock_level=10,
            unit="pcs"
        )

        self.prod_out = Product.objects.create(
            name="Gaming Headset",
            sku="HS-003",
            barcode="10003",
            category=self.category,
            supplier=self.supplier,
            cost_price=Decimal('30.00'),
            selling_price=Decimal('70.00'),
            current_stock=0, # Out of stock
            min_stock_level=5,
            unit="pcs"
        )

        self.customer = Customer.objects.create(
            name="Amit Kumar", phone="+91 98765 43211", email="amit@test.in"
        )

    def test_stock_status_properties(self):
        """Test product stock status flags and margin calculations."""
        self.assertFalse(self.prod_normal.is_low_stock)
        self.assertFalse(self.prod_normal.is_out_of_stock)
        self.assertEqual(self.prod_normal.stock_status, 'in_stock')
        self.assertEqual(self.prod_normal.margin_percentage, Decimal('60.0'))

        self.assertTrue(self.prod_low.is_low_stock)
        self.assertFalse(self.prod_low.is_out_of_stock)
        self.assertEqual(self.prod_low.stock_status, 'low_stock')

        self.assertFalse(self.prod_out.is_low_stock)
        self.assertTrue(self.prod_out.is_out_of_stock)
        self.assertEqual(self.prod_out.stock_status, 'out_of_stock')

    def test_automatic_stock_deduction_on_pos_sale(self):
        """Test that completing a POS sale automatically decrements inventory and logs stock movement."""
        initial_stock = self.prod_normal.current_stock # 30
        sold_qty = 3

        sale = process_pos_sale(
            items=[{
                'product_id': self.prod_normal.id,
                'quantity': sold_qty,
                'unit_price': self.prod_normal.selling_price,
                'discount': Decimal('0.00')
            }],
            customer=self.customer,
            customer_name=self.customer.name,
            customer_phone=self.customer.phone,
            tax_rate=Decimal('5.0'),
            discount_amount=Decimal('0.00'),
            payment_method='cash',
            cashier='Cashier 1'
        )

        # Refresh from database
        self.prod_normal.refresh_from_db()
        expected_stock = initial_stock - sold_qty
        self.assertEqual(self.prod_normal.current_stock, expected_stock)
        self.assertEqual(sale.subtotal, Decimal('150.00'))
        self.assertEqual(sale.tax_amount, Decimal('7.50'))
        self.assertEqual(sale.grand_total, Decimal('157.50'))
        self.assertEqual(sale.total_profit, Decimal('90.00'))

        # Verify StockMovement record
        movement = StockMovement.objects.filter(product=self.prod_normal, movement_type='sale').latest('created_at')
        self.assertEqual(movement.quantity, -sold_qty)
        self.assertEqual(movement.previous_stock, initial_stock)
        self.assertEqual(movement.new_stock, expected_stock)

    def test_pos_non_cash_payment_modes(self):
        """Test that card, upi, and credit/due sales record appropriate amount_paid and zero change."""
        # Test Card
        sale_card = process_pos_sale(
            items=[{'product_id': self.prod_normal.id, 'quantity': 1, 'unit_price': self.prod_normal.selling_price}],
            payment_method='card'
        )
        self.assertEqual(sale_card.payment_method, 'card')
        self.assertEqual(sale_card.amount_paid, sale_card.grand_total)
        self.assertEqual(sale_card.change_amount, Decimal('0.00'))

        # Test UPI
        sale_upi = process_pos_sale(
            items=[{'product_id': self.prod_normal.id, 'quantity': 1, 'unit_price': self.prod_normal.selling_price}],
            payment_method='upi'
        )
        self.assertEqual(sale_upi.payment_method, 'upi')
        self.assertEqual(sale_upi.amount_paid, sale_upi.grand_total)
        self.assertEqual(sale_upi.change_amount, Decimal('0.00'))

        # Test Due / Credit
        sale_due = process_pos_sale(
            items=[{'product_id': self.prod_normal.id, 'quantity': 1, 'unit_price': self.prod_normal.selling_price}],
            payment_method='due'
        )
        self.assertEqual(sale_due.payment_method, 'due')
        self.assertEqual(sale_due.amount_paid, Decimal('0.00'))
        self.assertEqual(sale_due.change_amount, Decimal('0.00'))

    def test_overselling_prevention(self):
        """Test that attempting to sell more items than available raises ValueError."""
        with self.assertRaises(ValueError):
            process_pos_sale(
                items=[{
                    'product_id': self.prod_normal.id,
                    'quantity': 100,
                    'unit_price': self.prod_normal.selling_price
                }]
            )

    def test_automatic_stock_increment_on_purchase(self):
        """Test that receiving a purchase order automatically increases product stock and updates cost."""
        initial_stock = self.prod_low.current_stock # 5
        purchase_qty = 20
        new_cost = Decimal('38.50')

        po = process_purchase_order(
            supplier=self.supplier,
            invoice_number="PO-TEST-001",
            items_data=[{
                'product_id': self.prod_low.id,
                'quantity': purchase_qty,
                'unit_cost': new_cost
            }],
            status='received'
        )

        self.prod_low.refresh_from_db()
        self.assertEqual(self.prod_low.current_stock, initial_stock + purchase_qty)
        self.assertEqual(self.prod_low.cost_price, new_cost)
        self.assertFalse(self.prod_low.is_low_stock)

        # Verify Stock Movement
        movement = StockMovement.objects.filter(product=self.prod_low, movement_type='purchase').latest('created_at')
        self.assertEqual(movement.quantity, purchase_qty)
        self.assertEqual(movement.previous_stock, initial_stock)
        self.assertEqual(movement.new_stock, initial_stock + purchase_qty)

    def test_authentication_and_route_protection(self):
        """Test that unauthenticated users are redirected to login, Super Admin sees only user and access, and staff see operational routes."""
        res = self.client.get(reverse('dashboard'))
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login/', res.url)

        # 1. Log in as Super Admin: should have access to user_list, and be redirected from operational views
        login_success = self.client.login(username='testadmin', password='pass123')
        self.assertTrue(login_success)

        # Super admin accesses User & Access portal
        res_users = self.client.get(reverse('user_list'))
        self.assertEqual(res_users.status_code, 200)

        # Super admin redirected from operational views to user_list
        res_dash = self.client.get(reverse('dashboard'))
        self.assertEqual(res_dash.status_code, 302)
        self.assertIn('/users/', res_dash.url)

        res_pos = self.client.get(reverse('pos'))
        self.assertEqual(res_pos.status_code, 302)
        self.assertIn('/users/', res_pos.url)

        # 2. Create staff manager user with operational permissions
        staff_user = User.objects.create_user('testmanager', 'manager@test.com', 'pass123', is_staff=True)
        staff_user.profile.can_access_pos = True
        staff_user.profile.can_manage_products = True
        staff_user.profile.can_manage_suppliers = True
        staff_user.profile.can_view_reports = True
        staff_user.profile.can_adjust_stock = True
        staff_user.profile.save()

        self.client.login(username='testmanager', password='pass123')
        operational_routes = [
            reverse('dashboard'),
            reverse('pos'),
            reverse('product_list'),
            reverse('low_stock_alerts'),
            reverse('supplier_list'),
            reverse('purchase_list'),
            reverse('sale_list'),
            reverse('stock_adjustment_list'),
            reverse('reports'),
        ]

        for route in operational_routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200, f"Route {route} failed with status {response.status_code}")

    def test_super_admin_user_crud(self):
        """Test Super Admin (Website Owner) user creation, modification, status toggle, and deletion."""
        self.client.login(username='testadmin', password='pass123')

        # 1. Create new user with granular permissions
        res_create = self.client.post(reverse('user_create'), {
            'username': 'newstaff',
            'first_name': 'New',
            'last_name': 'Employee',
            'email': 'staff@store.com',
            'password': 'password123',
            'role': 'manager',
            'is_active': True,
            'can_access_pos': True,
            'can_manage_products': True,
            'can_manage_suppliers': False,
            'can_view_reports': True,
            'can_adjust_stock': False,
        })
        self.assertEqual(res_create.status_code, 302)
        created_user = User.objects.get(username='newstaff')
        self.assertTrue(created_user.is_staff)
        self.assertFalse(created_user.is_superuser)
        self.assertTrue(created_user.profile.can_view_reports)
        self.assertFalse(created_user.profile.can_manage_suppliers)

        # 2. Modify user details and grant supplier permissions
        res_edit = self.client.post(reverse('user_update', kwargs={'pk': created_user.id}), {
            'first_name': 'Updated',
            'last_name': 'Employee',
            'email': 'updated@store.com',
            'role': 'admin',
            'is_active': True,
            'new_password': '',
            'can_access_pos': True,
            'can_manage_products': True,
            'can_manage_suppliers': True,
            'can_view_reports': True,
            'can_adjust_stock': True,
        })
        self.assertEqual(res_edit.status_code, 302)
        created_user.refresh_from_db()
        self.assertEqual(created_user.first_name, 'Updated')
        self.assertTrue(created_user.is_superuser)

        # 3. Toggle Status
        self.client.get(reverse('user_toggle_status', kwargs={'pk': created_user.id}))
        created_user.refresh_from_db()
        self.assertFalse(created_user.is_active)

        # 4. Delete user
        res_delete = self.client.post(reverse('user_delete', kwargs={'pk': created_user.id}))
        self.assertEqual(res_delete.status_code, 302)
        self.assertFalse(User.objects.filter(username='newstaff').exists())

    def test_non_superadmin_forbidden_from_user_management(self):
        """Test that regular staff/cashier users cannot access user management."""
        self.client.login(username='testcashier', password='pass123')
        res = self.client.get(reverse('user_list'))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('dashboard'))

    def test_granular_permission_enforcement(self):
        """Test that Website Owner's permission restrictions are actively enforced on cashier."""
        self.client.login(username='testcashier', password='pass123')
        
        # Cashier default has can_view_reports=False -> redirected
        res_reports = self.client.get(reverse('reports'))
        self.assertEqual(res_reports.status_code, 302)
        self.assertEqual(res_reports.url, reverse('dashboard'))

        # Website Owner grants can_view_reports=True to cashier
        self.regular_user.profile.can_view_reports = True
        self.regular_user.profile.save()

        # Now cashier can access reports!
        res_reports_ok = self.client.get(reverse('reports'))
        self.assertEqual(res_reports_ok.status_code, 200)

    def test_store_admin_crud_and_access_control(self):
        """Test Store Admin role: adding, modifying, toggling and deleting store branches."""
        from inventory.models import Store
        
        # 1. Cashier is blocked from store management
        self.client.login(username='testcashier', password='pass123')
        res_cashier = self.client.get(reverse('store_list'))
        self.assertEqual(res_cashier.status_code, 302)
        self.assertEqual(res_cashier.url, reverse('dashboard'))

        # 2. Create Store Admin user with can_manage_stores=True
        store_admin = User.objects.create_user('storelead', 'lead@test.com', 'pass123', is_staff=True)
        store_admin.profile.can_manage_stores = True
        store_admin.profile.role_title = "Store Admin"
        store_admin.profile.save()

        self.client.login(username='storelead', password='pass123')
        res_stores = self.client.get(reverse('store_list'))
        self.assertEqual(res_stores.status_code, 200)

        # 3. Add new store branch
        res_add = self.client.post(reverse('store_create'), {
            'name': 'Eastside Mall Branch',
            'code': 'STR-EAST-01',
            'manager_name': 'Rajesh Sharma',
            'phone': '+91 98765 43212',
            'city': 'Bengaluru, Karnataka',
            'is_main': False,
            'is_active': True
        })
        self.assertEqual(res_add.status_code, 302)
        new_store = Store.objects.get(code='STR-EAST-01')
        self.assertEqual(new_store.name, 'Eastside Mall Branch')

        # 4. Modify store branch details
        res_edit = self.client.post(reverse('store_update', kwargs={'pk': new_store.id}), {
            'name': 'Eastside Supercenter',
            'code': 'STR-EAST-01',
            'manager_name': 'Rajesh Sharma',
            'phone': '+91 98765 43213',
            'city': 'Bengaluru, Karnataka',
            'is_main': False,
            'is_active': True
        })
        self.assertEqual(res_edit.status_code, 302)
        new_store.refresh_from_db()
        self.assertEqual(new_store.name, 'Eastside Supercenter')

        # 5. Toggle store operational status
        self.client.get(reverse('store_toggle_status', kwargs={'pk': new_store.id}))
        new_store.refresh_from_db()
        self.assertFalse(new_store.is_active)

        # 6. Delete store branch
        res_del = self.client.post(reverse('store_delete', kwargs={'pk': new_store.id}))
        self.assertEqual(res_del.status_code, 302)
        self.assertFalse(Store.objects.filter(code='STR-EAST-01').exists())

    def test_currency_symbol_and_formatting(self):
        """Test that application uses Rs. currency symbol across context and templates."""
        from inventory.context_processors import inventory_globals
        ctx = inventory_globals(None)
        self.assertEqual(ctx.get('currency_symbol'), 'Rs.')

        # Verify Sale string representation uses Rs.
        sale = Sale.objects.create(
            invoice_number="INV-TEST-99",
            cashier="Cashier 1",
            subtotal=Decimal('100.00'),
            tax_rate=Decimal('0.00'),
            tax_amount=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            grand_total=Decimal('100.00'),
            amount_paid=Decimal('100.00'),
            change_amount=Decimal('0.00')
        )
        self.assertIn('Rs. 100.00', str(sale))

        # Test manager sees Rs. on dashboard
        mgr = User.objects.create_user('mgr_currency', 'mgr_curr@test.com', 'pass123', is_staff=True)
        self.client.login(username='mgr_currency', password='pass123')
        res = self.client.get(reverse('dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Rs.')

    def test_quick_category_and_supplier_api(self):
        """Test quick category and supplier AJAX creation from product form."""
        import json
        mgr = User.objects.create_user('mgr_quick', 'mgr_quick@test.com', 'pass123', is_staff=True)
        # Give profile permissions
        mgr.profile.can_manage_products = True
        mgr.profile.can_manage_suppliers = True
        mgr.profile.save()
        self.client.login(username='mgr_quick', password='pass123')

        # Test quick category
        res_cat = self.client.post(
            reverse('api_quick_category'),
            data=json.dumps({'name': 'Peripherals', 'description': 'Computer peripherals'}),
            content_type='application/json'
        )
        self.assertEqual(res_cat.status_code, 200)
        data_cat = res_cat.json()
        self.assertTrue(data_cat['success'])
        self.assertTrue(Category.objects.filter(name='Peripherals').exists())

        # Test quick supplier
        res_sup = self.client.post(
            reverse('api_quick_supplier'),
            data=json.dumps({
                'name': 'Delta Supplies Ltd',
                'contact_name': 'Sarah Connor',
                'phone': '+91 99999 11111',
                'email': 'sarah@delta.com',
                'address': 'Tech Park, Bangalore'
            }),
            content_type='application/json'
        )
        self.assertEqual(res_sup.status_code, 200)
        data_sup = res_sup.json()
        self.assertTrue(data_sup['success'])
        self.assertTrue(Supplier.objects.filter(name='Delta Supplies Ltd').exists())

    def test_expiry_date_tracking_and_dashboard_alerts(self):
        """Test product expiry date toggle, near expiry alerts, and dashboard warning banners."""
        from django.utils import timezone
        from datetime import timedelta
        from inventory.forms import ProductForm

        today = timezone.now().date()

        # Product with expiry in 10 days (near expiry)
        prod_expiring_soon = Product.objects.create(
            name="Organic Cow Milk 1L",
            sku="MLK-001",
            category=self.category,
            supplier=self.supplier,
            cost_price=Decimal('40.00'),
            selling_price=Decimal('65.00'),
            current_stock=25,
            min_stock_level=5,
            unit="ltr",
            has_expiry=True,
            expiry_date=today + timedelta(days=10)
        )

        # Product expired 3 days ago
        prod_expired = Product.objects.create(
            name="Greek Yogurt 500g",
            sku="YOG-002",
            category=self.category,
            supplier=self.supplier,
            cost_price=Decimal('50.00'),
            selling_price=Decimal('90.00'),
            current_stock=10,
            min_stock_level=5,
            unit="pcs",
            has_expiry=True,
            expiry_date=today - timedelta(days=3)
        )

        # Non-perishable product (has_expiry=False)
        self.assertFalse(self.prod_normal.has_expiry)
        self.assertFalse(self.prod_normal.is_expired)
        self.assertFalse(self.prod_normal.is_near_expiry)
        self.assertIsNone(self.prod_normal.expiry_badge_info)

        # Verify near-expiry properties
        self.assertTrue(prod_expiring_soon.has_expiry)
        self.assertTrue(prod_expiring_soon.is_near_expiry)
        self.assertFalse(prod_expiring_soon.is_expired)
        self.assertEqual(prod_expiring_soon.days_until_expiry, 10)
        self.assertIsNotNone(prod_expiring_soon.expiry_badge_info)

        # Verify expired properties
        self.assertTrue(prod_expired.has_expiry)
        self.assertTrue(prod_expired.is_expired)
        self.assertFalse(prod_expired.is_near_expiry)
        self.assertLess(prod_expired.days_until_expiry, 0)
        self.assertEqual(prod_expired.expiry_badge_info['status'], 'expired')

        # Test Form validation: when has_expiry is True, expiry_date is required
        form_invalid = ProductForm(data={
            'name': 'Test Item',
            'sku': 'TI-001',
            'cost_price': '10.00',
            'selling_price': '20.00',
            'current_stock': 10,
            'min_stock_level': 5,
            'unit': 'pcs',
            'has_expiry': True,
            'expiry_date': '',
            'is_active': True,
        })
        self.assertFalse(form_invalid.is_valid())
        self.assertIn('expiry_date', form_invalid.errors)

        # When has_expiry is False, expiry_date is cleared/optional
        form_valid = ProductForm(data={
            'name': 'Test Item 2',
            'sku': 'TI-002',
            'cost_price': '10.00',
            'selling_price': '20.00',
            'current_stock': 10,
            'min_stock_level': 5,
            'unit': 'pcs',
            'has_expiry': False,
            'expiry_date': '',
            'is_active': True,
        })
        self.assertTrue(form_valid.is_valid())

        # Test Dashboard shows alert banner and watchlist
        mgr = User.objects.create_user('mgr_expiry', 'mgr_expiry@test.com', 'pass123', is_staff=True)
        self.client.login(username='mgr_expiry', password='pass123')
        res = self.client.get(reverse('dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertIn('expired_count', res.context)
        self.assertGreaterEqual(res.context['expired_count'], 1)
        self.assertGreaterEqual(res.context['near_expiry_count'], 1)
        self.assertContains(res, 'Shelf-Life Warning: Product Expiry Alerts Triggered')
        self.assertContains(res, 'Organic Cow Milk 1L')
        self.assertContains(res, 'Greek Yogurt 500g')



