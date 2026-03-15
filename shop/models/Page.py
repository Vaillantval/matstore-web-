from django.db import models
from django.utils.text import slugify


class Page(models.Model):
    PAGE_TYPES = [
        ('about', 'À propos de nous'),
        ('terms', 'Conditions générales'),
        ('privacy', 'Politique de confidentialité'),
        ('general', 'Page générale'),
    ]

    name = models.CharField(max_length=120, blank=False, null=False)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=False, null=False)
    image = models.ImageField(upload_to='pages/%Y/%m/%d/', blank=True, null=True)
    page_type = models.CharField(max_length=20, choices=PAGE_TYPES, default='general')
    is_head = models.BooleanField(default=False)
    is_foot = models.BooleanField(default=False)
    is_checkout = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Page'
        verbose_name_plural = 'Pages'
