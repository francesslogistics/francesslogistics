import getpass

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Profile


class Command(BaseCommand):
    """
    Creates a staff login (User + Profile) directly in the database.

    This is intentionally a backend-only tool — there is no "add account"
    screen in the front-end. Positions are restricted to Profile.Position,
    so --position only accepts one of the four fixed job titles below
    (pass an invalid value and argparse will list the valid choices).

    Usage:
        python manage.py create_account jdoe --name "Juan Dela Cruz" --position "Sales Account Executive"
        python manage.py create_account jdoe --name "Juan Dela Cruz" --position CEO --password "..."
    """
    help = "Create a staff account (User + Profile) with a fixed job-title position. Backend-only — not exposed in the front-end."

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)
        parser.add_argument("--name", type=str, default="", help="Full name, e.g. \"Juan Dela Cruz\"")
        parser.add_argument(
            "--position",
            type=str,
            choices=[c[0] for c in Profile.Position.choices],
            required=True,
            help="One of the fixed job titles.",
        )
        parser.add_argument("--password", type=str, default=None, help="If omitted, you'll be prompted (input hidden).")

    def handle(self, *args, **options):
        username = options["username"]
        if User.objects.filter(username=username).exists():
            raise CommandError(f"A user named '{username}' already exists.")

        password = options["password"] or getpass.getpass("Password: ")
        if not password:
            raise CommandError("Password cannot be empty.")

        name = options["name"].strip()
        first, _, last = name.partition(" ")

        user = User.objects.create_user(username=username, password=password, first_name=first, last_name=last)
        Profile.objects.create(user=user, position=options["position"])

        self.stdout.write(self.style.SUCCESS(
            f"Created account '{username}' ({name or username}) — {options['position']}"
        ))
