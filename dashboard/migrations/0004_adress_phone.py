from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0003_alter_adress_author"),
    ]

    operations = [
        migrations.AddField(
            model_name="adress",
            name="phone",
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
