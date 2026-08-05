"""
Root URL configuration.

/admin/                     Django admin
/api/health/                simple health check
/api/settings/              global app settings (singleton)
/api/accounts/              login / logout / current-user profile
/api/billing/                CRUD for payables & receivables
/api/crm/                   CRUD for CRM agents/clients + nested contacts
/api/notifications/         CRUD for notification bell items
/api/trash/                 soft-deleted records (restore / purge)
/api/dashboard/...          KPI, chart, and BI report aggregation endpoints
"""
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve as static_serve
from core.views import dashboard_view, client_index_view, client_quote_view
from . import settings

urlpatterns = [
    path("admin/", admin.site.urls),

    # Public client-side (marketing) site — this is what visitors hit at
    # localhost:8000. The dashboard app now lives at /dashboard instead.
    path('', client_index_view, name='client-index'),
    path('index.html', client_index_view, name='client-index-html'),
    path('quote.html', client_quote_view, name='client-quote-html'),
    path('quote/', client_quote_view, name='client-quote'),
    path('assets/<path:path>', static_serve, {'document_root': settings.BASE_DIR / 'core' / 'site_assets' / 'assets'}),

    # Internal dashboard app — localhost:8000/dashboard
    path('dashboard', dashboard_view, name='dashboard'),
    path('dashboard/', dashboard_view),

    path("api/", include("core.urls")),
    path("api/quotations/", include("billing.urls_quotations")),
    path("api/accounts/", include("accounts.urls")),
    path("api/billing/", include("billing.urls")),
    path("api/crm/", include("crm.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/trash/", include("trash.urls")),
    path("api/dashboard/", include("dashboard.urls")),
]

# Serve uploaded inquiry files (10.5 dangerous-goods docs, 13 proof-of-goods).
urlpatterns += [
    path('media/<path:path>', static_serve, {'document_root': settings.MEDIA_ROOT}),
]
