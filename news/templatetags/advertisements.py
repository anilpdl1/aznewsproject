from django import template
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from news.models import Advertisement

register = template.Library()


@register.inclusion_tag("partials/_advertisement.html")
def advertisement_slot(placement):
    now = timezone.now()
    advertisement = (
        Advertisement.objects.filter(placement=placement, is_active=True)
        .filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
        .first()
    )
    return {
        "advertisement": advertisement,
        "adsense_client_id": getattr(settings, "ADSENSE_CLIENT_ID", ""),
        "adsense_slot_id": getattr(settings, "ADSENSE_SLOT_IDS", {}).get(placement, ""),
    }
