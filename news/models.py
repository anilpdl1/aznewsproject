from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="articles"
    )

    content = models.TextField()

    feature_image = models.ImageField(upload_to="news/", blank=True, null=True)

    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="articles"
    )

    tags = models.ManyToManyField(Tag, blank=True, related_name="articles")

    views_count = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

class Comment(models.Model):
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="comments"
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()

    @property
    def message(self):
        return self.content

    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.name} on {self.article.title}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} - {self.name}"


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-subscribed_at"]

    def __str__(self):
        return self.email


class ContentPage(models.Model):
    """Editable copy for informational pages such as About."""

    slug = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    image = models.ImageField(upload_to="pages/", blank=True, null=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class HomepageVideo(models.Model):
    title = models.CharField(max_length=200)
    video_id = models.CharField(max_length=20, help_text="YouTube video ID")
    category_label = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "pk"]

    def __str__(self):
        return self.title


class Advertisement(models.Model):
    class Placement(models.TextChoices):
        HEADER = "header", "Header banner"
        HOMEPAGE = "homepage", "Homepage"
        SIDEBAR = "sidebar", "Sidebar"
        ARTICLE = "article", "Article page"

    title = models.CharField(max_length=150)
    advertiser = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to="advertisements/")
    target_url = models.URLField()
    placement = models.CharField(max_length=20, choices=Placement.choices)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(blank=True, null=True)
    ends_at = models.DateTimeField(blank=True, null=True)
    priority = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-priority", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ends_at__isnull=True) | models.Q(starts_at__isnull=True) | models.Q(ends_at__gte=models.F("starts_at")),
                name="ad_end_after_start",
            )
        ]

    def __str__(self):
        return self.title

    def clean(self):
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValidationError({"ends_at": "End time must be on or after the start time."})
