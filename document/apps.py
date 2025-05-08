from django.apps import AppConfig


class DocumentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'document'

    def ready(self):
        # Import signal handlers
        import signals # type: ignore