import ipaddress
import json
import urllib.request

def get_client_ip(request):
    """Best-effort real client IP. Render (and most PaaS hosts) sit behind a
    proxy, so the actual visitor IP shows up in X-Forwarded-For rather than
    REMOTE_ADDR — take the first address in that chain when present."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _is_public_ip(ip):
    try:
        addr = ipaddress.ip_address(ip)
    except (ValueError, TypeError):
        return False
    return not (addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local)


def geolocate_ip(ip):
    """Resolves an IP to city/region/country using ipinfo.io's free,
    no-API-key endpoint. Deliberately best-effort: any failure (offline,
    rate-limited, private/loopback IP during local dev, timeout, etc.)
    just returns blanks rather than raising — a login should never fail
    because a geolocation lookup didn't work."""
    empty = {"city": "", "region": "", "country": ""}
    if not ip or not _is_public_ip(ip):
        return empty
    try:
        with urllib.request.urlopen(f"https://ipinfo.io/{ip}/json", timeout=3) as res:
            data = json.loads(res.read().decode("utf-8"))
        return {
            "city": data.get("city", "") or "",
            "region": data.get("region", "") or "",
            "country": data.get("country", "") or "",
        }
    except Exception:
        return empty


def log_login_activity(request, user):
    """Called right after a successful login — records the IP + resolved
    location. Wrapped in try/except at the call site too; this must never
    be able to break the login flow itself."""
    from .models import LoginActivity

    ip = get_client_ip(request)
    location = geolocate_ip(ip)
    LoginActivity.objects.create(user=user, ip_address=ip, **location)