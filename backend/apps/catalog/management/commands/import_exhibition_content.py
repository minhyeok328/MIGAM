from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from backend.data_pipeline.reviewed_content import import_reviewed_content, load_reviewed_content


class Command(BaseCommand):
    help = "Import reviewed official exhibition descriptions without changing canonical evidence."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="UTF-8 reviewed content JSON bundle")
        parser.add_argument("--dry-run", action="store_true", help="Validate the complete bundle without writing snapshots")

    def handle(self, *args, **options):
        try:
            result = import_reviewed_content(load_reviewed_content(options["file"]), dry_run=options["dry_run"])
        except (ValidationError, OSError, ValueError) as error:
            raise CommandError(str(error)) from error
        mode = "validated" if options["dry_run"] else "imported"
        self.stdout.write(f"{mode}: created={result.created} unchanged={result.unchanged}")
