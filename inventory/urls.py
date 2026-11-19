from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # POS / Billing Page
    path('pos/', views.pos_view, name='pos'),
    path('api/pos/checkout/', views.api_pos_checkout, name='api_pos_checkout'),
    path('api/pos/search/', views.api_search_products, name='api_pos_search'),
    path('api/pos/customer/quick/', views.api_quick_customer, name='api_quick_customer'),

    # Product Catalog & Low Stock
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('low-stock/', views.low_stock_view, name='low_stock_alerts'),

    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.supplier_update, name='supplier_update'),

    # Purchases / Stock In
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/add/', views.purchase_create, name='purchase_create'),
    path('purchases/<int:pk>/', views.purchase_detail, name='purchase_detail'),

    # Sales & Billing Records
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),

    # Stock Adjustments & Audit
    path('stock-adjustments/', views.stock_adjustment_list, name='stock_adjustment_list'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Super Admin: User Management
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_update, name='user_update'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/toggle-status/', views.user_toggle_status, name='user_toggle_status'),

    # Profit & Inventory Reports
    path('reports/', views.reports_view, name='reports'),
]

