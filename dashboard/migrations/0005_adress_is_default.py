from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0004_adress_phone"),
    ]

    operations = [
        migrations.AddField(
            model_name="adress",
            name="is_default",
            field=models.BooleanField(default=False),
        ),
    ]
