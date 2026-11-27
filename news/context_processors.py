"""Shared, request-scoped template context."""

from django.conf import settings

from .models import Category


def advertising_config(request):
    return {"ADSENSE_CLIENT_ID": getattr(settings, "ADSENSE_CLIENT_ID", "")}


def get_global_categories(request):
    """Return one ordered, lightweight category queryset per request."""
    if request.path.startswith(("/admin/", "/summernote/")):
        return Category.objects.none()
    categories = getattr(request, "_global_categories", None)
    if categories is None:
        categories = Category.objects.only("name", "slug").order_by("name")
        request._global_categories = categories
    return categories


def global_categories(request):
    return {"global_categories": get_global_categories(request)}


def social_links(request):
    from django.conf import settings

    configured_links = getattr(settings, "SOCIAL_LINKS", {})
    platforms = (
        ("facebook", "Facebook", "fab fa-facebook-f"),
        ("instagram", "Instagram", "fab fa-instagram"),
        ("youtube", "YouTube", "fab fa-youtube"),
        ("x", "X", "fab fa-twitter"),
    )
    return {
        "social_links": [
            {"platform": key, "label": label, "icon": icon, "url": configured_links.get(key, "")}
            for key, label, icon in platforms
            if configured_links.get(key)
        ]
    }
