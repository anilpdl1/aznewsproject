from django.contrib import admin
from django.utils.text import Truncator
from django_summernote.admin import SummernoteModelAdmin
from .models import (
    Article, Category, Comment, ContactMessage, ContentPage, HomepageVideo,
    Subscriber, Tag,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(Article)
class ArticleAdmin(SummernoteModelAdmin):
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
    search_fields = ("title", "content")
    date_hierarchy = "created_at"
    list_per_page = 25
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("views_count", "created_at", "updated_at")
    autocomplete_fields = ("author", "category", "tags")
    list_select_related = ("author", "category")
    summernote_fields = ("content",)


@admin.action(description="Approve selected comments")
def approve_comments(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.action(description="Reject / unapprove selected comments")
def reject_comments(modeladmin, request, queryset):
    queryset.update(is_approved=False)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("preview", "article", "name", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("name", "email", "content", "article__title")
    date_hierarchy = "created_at"
    list_per_page = 50
    list_editable = ("is_approved",)
    list_select_related = ("article",)
    actions = (approve_comments, reject_comments)

    @admin.display(description="Comment")
    def preview(self, obj):
        return Truncator(obj.content).chars(80)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    list_per_page = 50


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
