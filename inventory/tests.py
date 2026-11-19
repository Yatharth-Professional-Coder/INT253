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
            name="Alpha Supplies", contact_name="John V.", phone="+1 555-1234", email="john@alpha.com"
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
            name="Alice Walker", phone="555-9876", email="alice@test.com"
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
        """Test that unauthenticated users are redirected to login."""
        res = self.client.get(reverse('dashboard'))
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login/', res.url)

        # Log in as Super Admin
        login_success = self.client.login(username='testadmin', password='pass123')
        self.assertTrue(login_success)

        routes = [
            reverse('dashboard'),
            reverse('pos'),
            reverse('product_list'),
            reverse('low_stock_alerts'),
            reverse('supplier_list'),
            reverse('purchase_list'),
            reverse('sale_list'),
            reverse('stock_adjustment_list'),
            reverse('reports'),
            reverse('user_list'),
        ]

        for route in routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200, f"Route {route} failed with status {response.status_code}")

    def test_super_admin_user_crud(self):
        """Test Super Admin user creation, modification, status toggle, and deletion."""
        self.client.login(username='testadmin', password='pass123')

        # 1. Create new user
        res_create = self.client.post(reverse('user_create'), {
            'username': 'newstaff',
            'first_name': 'New',
            'last_name': 'Employee',
            'email': 'staff@store.com',
            'password': 'password123',
            'role': 'manager',
            'is_active': True
        })
        self.assertEqual(res_create.status_code, 302) # Redirects to user_list
        created_user = User.objects.get(username='newstaff')
        self.assertTrue(created_user.is_staff)
        self.assertFalse(created_user.is_superuser)

        # 2. Modify user details
        res_edit = self.client.post(reverse('user_update', kwargs={'pk': created_user.id}), {
            'first_name': 'Updated',
            'last_name': 'Employee',
            'email': 'updated@store.com',
            'role': 'admin',
            'is_active': True,
            'new_password': ''
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
        # Should redirect with access denied error
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('dashboard'))
