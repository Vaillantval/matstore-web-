from django.db import migrations, models


def deduplicate_product_slugs(apps, schema_editor):
    Product = apps.get_model('shop', 'Product')
    seen = {}
    for product in Product.objects.order_by('id'):
        original = product.slug
        if original in seen:
            n = 1
            candidate = f"{original}-{n}"
            while candidate in seen or Product.objects.filter(slug=candidate).exclude(pk=product.pk).exists():
                n += 1
                candidate = f"{original}-{n}"
            product.slug = candidate
            product.save(update_fields=['slug'])
        seen[product.slug] = True


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0015_fix_setting_copyright'),
    ]

    operations = [
        migrations.RunPython(deduplicate_product_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='product',
            name='slug',
            field=models.SlugField(max_length=255, unique=True),
        ),
    ]
