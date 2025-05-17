from django.core.management.base import BaseCommand
from django.apps import apps
from projects.models import Resource  # adjust if Resource is under a different app

class Command(BaseCommand):
    help = "Auto-creates Resource entries from installed models"

    def handle(self, *args, **options):
        app_labels = ['projects', 'accounts']  # ✅ Scan specific apps
        created = 0
        skipped = 0

        for app_label in app_labels:
            app_config = apps.get_app_config(app_label)
            for model in app_config.get_models():
                model_name = model.__name__
                model_code = model_name.lower()

                if Resource.objects.filter(code=model_code).exists():
                    self.stdout.write(f"Skipping existing resource: {model_code}")
                    skipped += 1
                    continue

                Resource.objects.create(
                    code=model_code,
                    name=model_name,
                    description=f"Auto-generated from {app_label}.{model_name}"
                )

                self.stdout.write(self.style.SUCCESS(f"Created resource: {model_code}"))
                created += 1

        self.stdout.write(self.style.NOTICE(f"✅ Done. Created: {created}, Skipped: {skipped}"))