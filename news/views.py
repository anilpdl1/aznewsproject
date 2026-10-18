from django.core.paginator import Paginator
from django.db.models import F
from django.shortcuts import get_object_or_404, render

from .models import Article, Category


def published_articles():
    return Article.objects.filter(is_published=True).select_related("author", "category")


def home(request):
    articles = published_articles()
    trending_articles = list(articles.filter(is_trending=True).order_by("-created_at", "-pk")[:9])
    whats_new_articles = list(articles.order_by("-created_at", "-pk")[:4])
    featured_ids = [article.pk for article in (*trending_articles, *whats_new_articles)]
    weekly_articles = list(
        articles.exclude(pk__in=featured_ids).order_by("-created_at", "-pk")[:4]
    )
    featured_ids.extend(article.pk for article in weekly_articles)
    weekly2_articles = list(
        articles.exclude(pk__in=featured_ids).order_by("-created_at", "-pk")[:5]
    )
    featured_ids.extend(article.pk for article in weekly2_articles)
    recent_articles = articles.exclude(pk__in=featured_ids).order_by("-created_at", "-pk")[:8]
    if not recent_articles.exists():
        recent_articles = articles.order_by("-created_at", "-pk")[:8]
    category_tabs = []
    for name in ("Lifestyle", "Travel", "Fashion", "Sports", "Technology"):
        category = Category.objects.filter(name__iexact=name).first()
        category_tabs.append({
            "name": name,
            "category": category,
            "articles": articles.filter(category=category).order_by("-created_at", "-pk")[:4]
            if category else Article.objects.none(),
        })
    return render(request, "index.html", {
        "trending_articles": trending_articles,
        "recent_articles": recent_articles,
        "whats_new_articles": whats_new_articles,
        "category_tabs": category_tabs,
        "weekly_articles": weekly_articles,
        "weekly2_articles": weekly2_articles,
    })


def category(request, slug):
    selected_category = get_object_or_404(Category, slug=slug)
    article_list = published_articles().filter(category=selected_category).order_by("-created_at", "-pk")
    page_obj = Paginator(article_list, 10).get_page(request.GET.get("page"))
    return render(request, "categori.html", {"category": selected_category, "page_obj": page_obj, "articles": page_obj.object_list})


def latest_news(request):
    article_list = published_articles().order_by("-created_at", "-pk")
    page_obj = Paginator(article_list, 10).get_page(request.GET.get("page"))
    return render(request, "latest_news.html", {"page_obj": page_obj, "articles": page_obj.object_list})


def details(request, slug):
    article = get_object_or_404(published_articles(), slug=slug)
    Article.objects.filter(pk=article.pk).update(views_count=F("views_count") + 1)
    article.refresh_from_db(fields=("views_count",))
    related_articles = published_articles().filter(category=article.category).exclude(pk=article.pk).order_by("-created_at", "-pk")[:4]
    return render(request, "single-blog.html", {"article": article, "related_articles": related_articles})


def about(request):
    return render(request,'about.html')
def contact(request):
    return render(request,'contact.html')

