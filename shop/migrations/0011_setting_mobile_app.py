from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0010_method_order_orderdetail"),
    ]

    operations = [
        migrations.AddField(
            model_name="setting",
            name="show_app_banner",
            field=models.BooleanField(
                default=False,
                help_text="Afficher le bandeau de téléchargement de l'app dans le header.",
            ),
        ),
        migrations.AddField(
            model_name="setting",
            name="apk_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="mobile/apk/",
                help_text="Fichier APK Android (.apk).",
            ),
        ),
        migrations.AddField(
            model_name="setting",
            name="apk_version",
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                help_text="Ex : 1.0.0",
            ),
        ),
        migrations.AddField(
            model_name="setting",
            name="apk_description",
            field=models.CharField(
                blank=True,
                default="Téléchargez notre application mobile",
                max_length=120,
                null=True,
                help_text="Texte d'invitation affiché dans le bandeau.",
            ),
        ),
    ]
