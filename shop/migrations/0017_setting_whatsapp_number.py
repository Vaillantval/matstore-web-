from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0016_product_slug_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='setting',
            name='whatsapp_number',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=20,
                help_text="Numéro WhatsApp au format international sans espaces (ex : +50912345678). Laisser vide pour masquer le bouton.",
            ),
        ),
    ]
