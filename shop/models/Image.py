import io
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image as PilImage

from shop.models.Product import Product


class Image(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="product_images/%Y/%m/%d/", blank=False, null=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.image and hasattr(self.image, 'file'):
            img = PilImage.open(self.image)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            # Redimensionner si plus large que 800px (taille max pour une image produit)
            max_width = 800
            if img.width > max_width:
                ratio = max_width / img.width
                img = img.resize((max_width, int(img.height * ratio)), PilImage.LANCZOS)
            output = io.BytesIO()
            img.save(output, format='WEBP', quality=82, optimize=True)
            output.seek(0)
            name_without_ext = self.image.name.rsplit('.', 1)[0].split('/')[-1]
            self.image.save(f"{name_without_ext}.webp", ContentFile(output.read()), save=False)
        super().save(*args, **kwargs)
