"""
Aggregation endpoints that power the dashboard's KPI cards, charts, and
BI reports. Every number here is computed live from the database with
Django's ORM aggregates — with an empty database every response is 0 /
empty, exactly like a brand-new install of the front-end.
"""
from calendar import month_abbr
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from billing.models import BillingRecord


def _php_records():
    return BillingRecord.objects.filter(currency=BillingRecord.Currency.PHP)


def _last_n_months(n):
    today = timezone.localdate().replace(day=1)
    months = []
    y, m = today.year, today.month
    for i in range(n - 1, -1, -1):
        mm = m - i
        yy = y
        while mm <= 0:
            mm += 12
            yy -= 1
        months.append((yy, mm))
    return months


def _month_label(y, m):
    return f"{month_abbr[m]} {str(y)[-2:]}"


@api_view(["GET"])
def kpis(request):
    """Dashboard's 3 top KPI cards."""
    qs = BillingRecord.objects

    def bucket(category, status):
        rows = qs.filter(category=category, status=status)
        agg = rows.aggregate(count=Count("id"), amount=Sum("amount"))
        return {"count": agg["count"] or 0, "amount": float(agg["amount"] or 0)}

    payables_outstanding = bucket(BillingRecord.Category.PAYABLE, BillingRecord.Status.OUTSTANDING)
    receivables_outstanding = bucket(BillingRecord.Category.RECEIVABLE, BillingRecord.Status.OUTSTANDING)
    overdue_agg = qs.filter(status=BillingRecord.Status.OVERDUE).aggregate(count=Count("id"), amount=Sum("amount"))

    return Response({
        "outstanding_payables": payables_outstanding,
        "outstanding_receivables": receivables_outstanding,
        "overdue_invoices": {
            "count": overdue_agg["count"] or 0,
            "amount": float(overdue_agg["amount"] or 0),
        },
    })


def _build_bar_chart():
    """Payables vs receivables transaction count per month (last 6 months)."""
    months = _last_n_months(6)
    labels, payables, receivables = [], [], []
    for y, m in months:
        labels.append(_month_label(y, m))
        payables.append(BillingRecord.objects.filter(category="payable", invoice_date__year=y, invoice_date__month=m).count())
        receivables.append(BillingRecord.objects.filter(category="receivable", invoice_date__year=y, invoice_date__month=m).count())
    return {"labels": labels, "payables": payables, "receivables": receivables}


def _build_line_chart():
    """Annual revenue — receivables billed per month, current calendar year, PHP only."""
    year = timezone.localdate().year
    labels, revenue = [], []
    for m in range(1, 13):
        labels.append(_month_label(year, m))
        total = _php_records().filter(category="receivable", invoice_date__year=year, invoice_date__month=m).aggregate(s=Sum("amount"))["s"] or 0
        revenue.append(float(total))
    return {"labels": labels, "revenue": revenue}


@api_view(["GET"])
def bar_chart(request):
    return Response(_build_bar_chart())


@api_view(["GET"])
def line_chart(request):
    return Response(_build_line_chart())


@api_view(["GET"])
def pie_chart(request):
    """This month's invoice status composition (PHP only)."""
    today = timezone.localdate()
    qs = _php_records().filter(invoice_date__year=today.year, invoice_date__month=today.month)
    counts = {s: qs.filter(status=s).count() for s in ["paid", "outstanding", "overdue"]}
    return Response({
        "labels": ["Paid", "Outstanding", "Overdue"],
        "data": [counts["paid"], counts["outstanding"], counts["overdue"]],
    })


@api_view(["GET"])
def revenue_analytics(request):
    """Revenue analytics side panel (PHP only)."""
    today = timezone.localdate()
    year_qs = _php_records().filter(category="receivable", invoice_date__year=today.year)
    ytd_total = year_qs.aggregate(s=Sum("amount"))["s"] or 0
    month_total = year_qs.filter(invoice_date__month=today.month).aggregate(s=Sum("amount"))["s"] or 0

    months_with_data = year_qs.filter(invoice_date__month__lte=today.month).values_list("invoice_date__month", flat=True).distinct().count()
    avg_monthly = (ytd_total / months_with_data) if months_with_data else 0

    top_client_row = (
        year_qs.values("client")
        .annotate(total=Sum("amount"))
        .order_by("-total")
        .first()
    )
    top_client = top_client_row["client"] if top_client_row else None

    return Response({
        "total_revenue_ytd": float(ytd_total),
        "this_month": float(month_total),
        "avg_monthly_ytd": float(avg_monthly),
        "top_client_ytd": top_client,
    })


@api_view(["GET"])
def this_month(request):
    """'This month' summary card at the bottom of the dashboard."""
    today = timezone.localdate()
    qs = BillingRecord.objects.filter(invoice_date__year=today.year, invoice_date__month=today.month)
    created = qs.count()
    settled = qs.filter(status="paid").count()
    outstanding_amt = BillingRecord.objects.filter(status__in=["outstanding", "overdue"]).aggregate(s=Sum("amount"))["s"] or 0
    return Response({
        "invoices_created": created,
        "invoices_settled": settled,
        "total_outstanding": float(outstanding_amt),
    })


# ─────────────────────────────────────────────
# BI REPORTS  (view-bi tab)
# ─────────────────────────────────────────────

@api_view(["GET"])
def report_volume(request):
    """Monthly volume — payables vs receivables count, last 6 months."""
    return Response(_build_bar_chart())


@api_view(["GET"])
def report_revenue(request):
    """Annual revenue line chart — same series as the dashboard's line chart."""
    return Response(_build_line_chart())


@api_view(["GET"])
def report_ontime(request):
    """Payment timeliness doughnut — status breakdown across ALL records."""
    counts = BillingRecord.objects.values("status").annotate(n=Count("id"))
    lookup = {row["status"]: row["n"] for row in counts}
    return Response({
        "labels": ["Paid", "Outstanding", "Overdue"],
        "data": [lookup.get("paid", 0), lookup.get("outstanding", 0), lookup.get("overdue", 0)],
    })


@api_view(["GET"])
def report_vendor(request):
    """Top 8 vendors by payable spend, PHP only."""
    rows = (
        BillingRecord.objects
        .filter(category="payable", currency="PHP")
        .exclude(vendor="")
        .values("vendor")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:8]
    )
    return Response({
        "labels": [r["vendor"] for r in rows],
        "data": [float(r["total"]) for r in rows],
    })
