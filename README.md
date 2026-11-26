# SmartStock Pro &mdash; Smart Inventory Management & POS Billing System

A comprehensive, production-ready **Smart Inventory Management & Point of Sale (POS) System** built with **Django** and **SQL (SQLite)**. Designed to give businesses real-time visibility, automated inventory synchronizations, low-stock threshold alerts, purchasing workflows, sales tracking, and rich profit analytics.

---

## 🌟 Key Features

### 1. ⚡ High-Speed POS Billing Terminal (`/pos/`)
* **Real-Time Barcode & Name Search**: Instant search and barcode scanner support (press `F2` to focus). Scanning an exact barcode immediately adds the item to the cart.
* **Interactive Cart**: Quantity adjustment steppers (`+` / `-`), line subtotal calculations, and item removals.
* **Smart Calculations**: Configurable sales tax rates (`0%`, `5%`, `10%`, `12%`, `18%`), instant discounts, and real-time Grand Total updates.
* **Payment Flexibility**: Support for Cash, Credit/Debit Card, UPI / QR Code, and Credit / Due.
* **Cash Tender Calculator**: Live change return calculation (e.g., Given Rs. 500 &rarr; Change Rs. 120.00).
* **Instant Tax Invoice & Receipt Modal**: Automatically pops up post-transaction with print formatting for both thermal receipt printers and standard A4 sheets.
* **Quick Customer Creation**: Add new customer profiles without leaving the POS register.

### 2. 🔄 Automatic Stock Updates (Zero Discrepancies)
* **On POS Billing / Sale**: On-hand product inventory is atomically decreased (`product.current_stock -= quantity`). If an item is out of stock, overselling is prevented.
* **On Purchase Order Receipt**: Receiving inbound shipments automatically increments stock (`product.current_stock += quantity`) and updates the product's latest purchase cost.
* **Comprehensive Audit Trail (`/stock-adjustments/`)**: Every stock change is permanently logged in the database (`StockMovement`) with timestamps, quantities, previous stock, new stock, and reference IDs (Invoice # / PO #).

### 3. 🚨 Automated Low-Stock Alerts Center (`/low-stock/`)
* **Dynamic Warning Badges**: The navigation bar displays a live alert counter across every page.
* **Threshold Rules**: Products with stock &le; `min_stock_level` are categorized into **Low Stock** (yellow) or **Out of Stock** (red).
* **One-Click Restocking**: Direct `Restock` shortcuts pre-populate a new Supplier Purchase Order with the deficit quantity.

### 4. 📦 Products & Catalog Management (`/products/`)
* Full CRUD (Create, Read, Update, Delete) for inventory products.
* Track SKU, Barcode, Category, Supplier, Cost Price, Selling Price, Margin %, Current Stock, and Min Stock Alert Level.
* Filter by Category, Stock Status (In Stock, Low Stock, Out of Stock), or search by keyword.

### 5. 🚚 Supplier & Purchase Management (`/suppliers/` & `/purchases/`)
* Supplier directory with contact persons, phone numbers, emails, and address records.
* Dynamic multi-item Purchase Order builder with live line-cost calculation.
* Manage order statuses (`Received`, `Pending`, `Cancelled`).

### 6. 📊 Profit, Revenue & Inventory Valuation Reports (`/reports/`)
* **Timeframe Filters**: Today, Last 7 Days, This Month, Last 30 Days, This Year, and All Time.
* **Financial P&L Breakdown**:
  * Total Gross Revenue
  * Cost of Goods Sold (COGS)
  * Net Gross Profit
  * Gross Profit Margin (%)
* **Inventory Valuation**:
  * Total units on shelves
  * Valuation at Cost (Capital tied in inventory)
  * Valuation at Retail (Total expected sales value)
  * Projected Future Unrealized Profit
* **Top Selling Products**: Ranked by units sold, total revenue, COGS, profit, and margin.
* **Category Breakdown & Payment Distribution**: Visual progress bars and breakdown by payment mode.

### 7. 🏪 Multi-Store & Retail Branch Management (`/stores/`)
* **Multi-Location Architecture**: Complete support for retail chains, franchises, and regional branches (e.g. Flagship HQ, Downtown Branch, Westside Outlet).
* **Dedicated Store Admin Role**:
  * Users with the `Store Admin` role can create new stores, update store contact and address details, and view store branch performance.
  * Website Owners (Super Admin) maintain full control to assign managers and toggle active status.
* **Store Deletion Guardrails**: Protected against accidental deletion of the primary headquarters (`is_main=True`) or stores with historical transaction ledgers.
* **Branch-Tagged Transactions**: All purchases, sales, and employee user profiles are linked directly to designated branch stores.

### 8. 🔐 User Authentication & Super Admin Control Center (`/users/`)
* **Dedicated Sign-In Page (`/login/`)**: Modern authentication portal with error alerts, remember credentials, and one-click quick-fill demo pills.
* **Website Owner (Super Admin) Control Center (`/users/`)**:
  * Exclusively accessible by the Website Owner (`is_superuser=True`). Regular staff and cashiers are automatically blocked with a 403 / redirect.
  * **Granular Permission Matrix**: Toggle individual module rights per user (`Can Manage Stores`, `Can Manage Products`, `Can Manage Suppliers`, `Can View Reports`, `Can Access POS`, `Can Adjust Stock`).
  * **View All Users**: Real-time table displaying usernames, full names, email addresses, system role badges, assigned branch store, account active status, and timestamps.
  * **Create New Users**: Add system users with roles (`Website Owner`, `Store Admin`, `Store Manager`, `POS Cashier`). Passwords are automatically hashed and saved securely.
  * **Modify / Edit User Details**: Update user names, emails, role assignments, store assignments, and reset user passwords directly from the dashboard.
  * **1-Click Status Toggle**: Activate or deactivate user access instantly.
  * **Safe Deletion with Guardrails**: Safeguards prevent accidental self-deletion of the active Super Admin.

---

## 🛠️ Technology Stack
* **Backend**: Python 3, Django 4.2+ (Django Auth, Sessions, ORM)
* **Database (SQL)**: Relational SQLite (`db.sqlite3`), with full ORM transactional integrity (`@transaction.atomic`)
* **Frontend**: HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons
* **Visualizations**: Chart.js 4.4+ (Sales trajectories & revenue curves)

---

## 🚀 Quick Start Guide

### 1. Launch the Server
You can launch the system with the provided script:
```bash
./start.sh
```
Or manually run:
```bash
./venv/bin/python manage.py runserver 127.0.0.1:8000
```

### 2. Access the Application
Open your browser and navigate to:
* **Login Page**: [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)
* **Super Admin Portal (User & Access Control)**: [http://127.0.0.1:8000/users/](http://127.0.0.1:8000/users/)
* **Multi-Store Management (Store Admin)**: [http://127.0.0.1:8000/stores/](http://127.0.0.1:8000/stores/)
* **Dashboard (Staff & Managers)**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **POS Billing Terminal**: [http://127.0.0.1:8000/pos/](http://127.0.0.1:8000/pos/)
* **Django Admin**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

### 3. Website Owner Credentials
The system initializes with a clean, production-ready database (zero demo items/sales). Use the initial Website Owner account to log in and configure your staff accounts and store branches:

| Role | Username | Password | Dedicated Scope |
| :--- | :--- | :--- | :--- |
| **Website Owner (Super Admin)** | `admin` | `admin123` | **Strictly User & Access Management**: Add/modify users, grant granular permissions, and appoint Store Admins. |

---

## 🧪 Automated Test Suite
Run the test suite at any time:
```bash
./venv/bin/python manage.py test
```
All automated tests verify:
1. Automatic stock deduction upon sale checkout.
2. Inability to oversell past available stock.
3. Automatic stock increment upon receiving purchase orders.
4. Correct calculation of COGS, gross margins, and inventory valuation.
5. Live route rendering status (HTTP 200).

---

## 📂 Project Structure
```text
untitled folder/
├── manage.py
├── start.sh                      # One-click startup script
├── db.sqlite3                    # SQL relational database pre-seeded with data
├── inventory/
│   ├── models.py                 # Category, Supplier, Product, Customer, Purchase, Sale, StockMovement
│   ├── views.py                  # Dashboard, POS, Products, Alerts, Reports, CRUD views
│   ├── services.py               # Atomic inventory business logic (sale deduction, purchase receipt)
│   ├── context_processors.py     # Live low-stock alert counter across all pages
│   ├── forms.py                  # Product, Supplier, Stock adjustment forms
│   ├── urls.py                   # URL routing
│   ├── admin.py                  # Django admin customization
│   ├── tests.py                  # Automated unit test suite
│   └── management/commands/
│       └── seed_data.py          # Realistic database seeder
├── smart_inventory/
│   ├── settings.py               # Django settings configuration
│   ├── urls.py                   # Root URLs
│   └── wsgi.py
└── templates/
    └── inventory/
        ├── base.html             # Master layout with responsive navbar & alert badges
        ├── login.html            # Dedicated user authentication & quick-fill role portal
        ├── dashboard.html        # Executive KPIs, 7-day sales chart, critical stock alerts
        ├── store_list.html       # Multi-Store branches overview & management
        ├── store_form.html       # Add / edit retail store branch
        ├── user_list.html        # Website Owner user & permission matrix
        ├── user_form.html        # Add / edit user and granular access control
        ├── pos.html              # Flagship POS Billing Terminal with barcode scan & cart
        ├── product_list.html     # Inventory catalog table with filters
        ├── product_form.html     # Add/edit product
        ├── low_stock_alerts.html # Alerts center with one-click restock
        ├── supplier_list.html    # Suppliers directory
        ├── supplier_form.html    # Add/edit supplier
        ├── purchase_list.html    # Inbound PO shipments
        ├── purchase_form.html    # Multi-product PO builder
        ├── purchase_detail.html  # Supplier PO invoice
        ├── sale_list.html        # Sales invoices ledger
        ├── sale_receipt.html     # Tax invoice & printable thermal receipt
        ├── stock_adjustments.html# Audit trail & manual adjustments
        └── reports.html          # Financial P&L and Inventory Valuation analytics
```

