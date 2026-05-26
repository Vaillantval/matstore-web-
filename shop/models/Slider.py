import io
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image


class Slider(models.Model):
    title = models.CharField(max_length=60, blank=False, null=False)
    description = models.CharField(max_length=120,blank=False, null=False)
    button_text=  models.CharField(max_length=60,blank=False, null=False)
    button_link = models.CharField(max_length=255,blank=False, null=False)
    image = models.ImageField(upload_to="sliders/%Y/%m/%d/",blank=False, null=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.image and hasattr(self.image, 'file'):
            img = Image.open(self.image)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            # Redimensionner si plus large que 1400px (taille max raisonnable pour un slider)
            max_width = 1400
            if img.width > max_width:
                ratio = max_width / img.width
                img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
            output = io.BytesIO()
            img.save(output, format='WEBP', quality=82, optimize=True)
            output.seek(0)
            name_without_ext = self.image.name.rsplit('.', 1)[0].split('/')[-1]
            self.image.save(f"{name_without_ext}.webp", ContentFile(output.read()), save=False)
        super().save(*args, **kwargs)

