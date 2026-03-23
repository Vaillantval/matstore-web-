from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"

    def ready(self):
        from notifications.firebase_config import initialize_firebase
        initialize_firebase()
        import notifications.signals  # noqa: F401
