from django.contrib import admin
from .models import (
    Article, Category, Comment, ContactMessage, ContentPage, HomepageVideo,
    Subscriber, Tag,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "category",
        "is_published",
        "is_trending",
        "views_count",
        "created_at",
    )
    list_filter = ("is_published", "is_trending", "category", "created_at")
    search_fields = ("title", "content", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("name", "article", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("name", "email", "content")
    list_editable = ("is_approved",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("created_at",)


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "subscribed_at")
    list_filter = ("is_active", "subscribed_at")
    search_fields = ("email",)
    list_editable = ("is_active",)


@admin.register(ContentPage)
class ContentPageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published")
    list_filter = ("is_published",)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(HomepageVideo)
class HomepageVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "category_label", "is_active", "position")
    list_filter = ("is_active",)
    list_editable = ("is_active", "position")
    search_fields = ("title", "description", "video_id")
