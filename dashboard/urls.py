from django.urls import path
from . import views

urlpatterns = [
    path("kpis/", views.kpis, name="dashboard-kpis"),
    path("charts/bar/", views.bar_chart, name="dashboard-bar-chart"),
    path("charts/line/", views.line_chart, name="dashboard-line-chart"),
    path("charts/pie/", views.pie_chart, name="dashboard-pie-chart"),
    path("revenue-analytics/", views.revenue_analytics, name="dashboard-revenue-analytics"),
    path("this-month/", views.this_month, name="dashboard-this-month"),

    path("reports/volume/", views.report_volume, name="report-volume"),
    path("reports/revenue/", views.report_revenue, name="report-revenue"),
    path("reports/ontime/", views.report_ontime, name="report-ontime"),
    path("reports/vendor/", views.report_vendor, name="report-vendor"),
]
