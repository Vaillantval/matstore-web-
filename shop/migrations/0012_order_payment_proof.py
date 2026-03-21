from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0011_setting_mobile_app'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_proof',
            field=models.ImageField(blank=True, null=True, upload_to='order_proofs/'),
        ),
    ]
