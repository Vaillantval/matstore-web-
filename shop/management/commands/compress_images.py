import io
import os
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image as PilImage


def _compress(image_field, max_width, label):
    try:
        image_field.open('rb')
        raw = image_field.read()
        image_field.close()
    except Exception as e:
        return False, f"lecture impossible : {e}"

    try:
        img = PilImage.open(io.BytesIO(raw))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), PilImage.LANCZOS)
        output = io.BytesIO()
        img.save(output, format='WEBP', quality=82, optimize=True)
        output.seek(0)
        name_without_ext = image_field.name.rsplit('.', 1)[0].split('/')[-1]
        new_name = f"{name_without_ext}.webp"
        image_field.save(new_name, ContentFile(output.read()), save=True)
        return True, f"{len(raw)//1024} KB → {output.tell()//1024} KB"
    except Exception as e:
        return False, str(e)


class Command(BaseCommand):
    help = "Recompresse toutes les images existantes (sliders + produits) en WebP."

    def handle(self, *args, **kwargs):
        from shop.models.Slider import Slider
        from shop.models.Image import Image

        self.stdout.write(self.style.MIGRATE_HEADING("── Sliders ──"))
        sliders = Slider.objects.exclude(image='')
        for slider in sliders:
            ok, info = _compress(slider.image, max_width=1400, label=slider.title)
            if ok:
                self.stdout.write(self.style.SUCCESS(f"  ✓ {slider.title} : {info}"))
            else:
                self.stdout.write(self.style.ERROR(f"  ✗ {slider.title} : {info}"))

        self.stdout.write(self.style.MIGRATE_HEADING("── Images produit ──"))
        images = Image.objects.exclude(image='').select_related('product')
        total, errors = 0, 0
        for img_obj in images:
            ok, info = _compress(img_obj.image, max_width=800, label=str(img_obj.pk))
            if ok:
                total += 1
                self.stdout.write(f"  ✓ produit [{img_obj.product.name}] : {info}")
            else:
                errors += 1
                self.stdout.write(self.style.ERROR(f"  ✗ image #{img_obj.pk} : {info}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nTerminé — {len(sliders)} sliders, {total} images produit converties, {errors} erreur(s)."
        ))
