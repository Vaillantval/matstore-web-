from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="fcm_token",
            field=models.CharField(
                blank=True,
                max_length=512,
                null=True,
                help_text="Firebase Cloud Messaging token pour les push notifications Flutter.",
            ),
        ),
        migrations.AddField(
            model_name="customer",
            name="phone",
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
