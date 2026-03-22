from django.core.exceptions import ValidationError


def validate_apk_extension(value):
    if not value.name.lower().endswith('.apk'):
        raise ValidationError("Seuls les fichiers .apk sont acceptés.")
