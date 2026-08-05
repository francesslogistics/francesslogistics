from django.core.management.base import BaseCommand
from trash.models import TrashedItem


class Command(BaseCommand):
    """
    Permanently deletes any TrashedItem past its retention window.
    Run this on a daily cron / scheduled task, e.g.:

        0 3 * * *  /path/to/venv/bin/python manage.py purge_trash

    (The Trash API also self-purges expired rows on every GET /api/trash/
    call, so this command is a belt-and-braces backup for installs that
    rarely open the Trash tab.)
    """
    help = "Permanently delete trashed records older than TRASH_RETENTION_DAYS."

    def handle(self, *args, **options):
        expired_ids = [item.id for item in TrashedItem.objects.all() if item.is_expired]
        count = len(expired_ids)
        TrashedItem.objects.filter(id__in=expired_ids).delete()
        self.stdout.write(self.style.SUCCESS(f"Purged {count} expired trash item(s)."))
