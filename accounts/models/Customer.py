from django.contrib.auth.models import AbstractUser
from django.db import models


class Customer(AbstractUser):
    agree_terms = models.BooleanField(default=False)
    phone = models.CharField(max_length=30, blank=True, null=True)
    fcm_token = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        help_text="Firebase Cloud Messaging token pour les push notifications Flutter.",
    )