from django.db.models import F
from .models import Product

def inventory_globals(request):
    """Global context available across all Django templates."""
    try:
        low_stock_count = Product.objects.filter(current_stock__gt=0, current_stock__lte=F('min_stock_level'), is_active=True).count()
        out_of_stock_count = Product.objects.filter(current_stock__lte=0, is_active=True).count()
    except Exception:
        low_stock_count = 0
        out_of_stock_count = 0

    return {
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_stock_alerts': low_stock_count + out_of_stock_count,
        'app_name': 'SmartStock POS & Inventory',
        'currency_symbol': 'Rs.',
    }
