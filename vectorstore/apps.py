from django.apps import AppConfig

class VectorStoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vectorstore'
    
    def ready(self):
        # Import signal handlers
        import vectorstore.signals # type: ignore