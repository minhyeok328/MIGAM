from django.core.management.base import BaseCommand

from backend.apps.discovery.projection import rebuild_search_documents


class Command(BaseCommand):
    help = "Rebuild the SQLite FTS5 search projection from canonical records."

    def handle(self, *args: object, **options: object) -> None:
        summary = rebuild_search_documents()
        self.stdout.write(
            self.style.SUCCESS(
                "Search index rebuilt: "
                f"{summary.exhibition_count} exhibitions, "
                f"{summary.institution_count} institutions."
            )
        )
