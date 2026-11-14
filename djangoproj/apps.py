"""Project-specific app configuration for third-party Django apps."""

from django_summernote.apps import DjangoSummernoteConfig


class ProjectSummernoteConfig(DjangoSummernoteConfig):
    # django-summernote's historical migration uses AutoField for Attachment.id.
    default_auto_field = "django.db.models.AutoField"
