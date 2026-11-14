"""Template filters for safely rendering formatted editorial content."""

import bleach
from bleach.css_sanitizer import CSSSanitizer
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_ALLOWED_TAGS = {
    "a", "b", "blockquote", "br", "code", "div", "em", "h1", "h2",
    "h3", "h4", "h5", "h6", "hr", "i", "img", "li", "ol", "p",
    "pre", "s", "span", "strike", "strong", "sub", "sup", "table",
    "tbody", "td", "th", "thead", "tr", "u", "ul",
}
_ALLOWED_ATTRIBUTES = {
    "*": ("class", "title"),
    "a": ("href", "target", "rel"),
    "img": ("src", "alt", "width", "height"),
    "p": ("style",),
    "h1": ("style",),
    "h2": ("style",),
    "h3": ("style",),
    "h4": ("style",),
    "h5": ("style",),
    "h6": ("style",),
    "div": ("style",),
    "span": ("style",),
    "td": ("style",),
    "th": ("style",),
}
_CSS_SANITIZER = CSSSanitizer(allowed_css_properties={
    "background-color", "color", "font-size", "font-style", "font-weight",
    "text-align", "text-decoration", "vertical-align",
})


@register.filter
def rich_text(value):
    """Render Summernote HTML after removing unsafe markup and attributes."""
    cleaned = bleach.clean(
        str(value or ""),
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        protocols={"http", "https", "mailto"},
        css_sanitizer=_CSS_SANITIZER,
        strip=True,
    )
    return mark_safe(cleaned)
