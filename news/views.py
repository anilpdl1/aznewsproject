from django.core.paginator import Paginator
from django.db.models import F
from django.shortcuts import get_object_or_404, render

from .models import Article, Category

YOUTUBE_VIDEOS = (
    "CicQIuG8hBo",
    "rIz00N40bag",
    "CONfhrASy44",
    "lq6fL2ROWf8",
    "0VxlQlacWV4",
)


def published_articles():
    return Article.objects.filter(is_published=True).select_related("author", "category")


def home(request):
    articles = published_articles()
    ordering = ("-created_at", "-pk")
    latest_articles = articles.order_by(*ordering)
    trending_articles = list(articles.filter(is_trending=True).order_by(*ordering)[:9])
    all_published_articles = latest_articles
    recent_articles = latest_articles[:4]
    weekly_articles = recent_articles
    ticker_articles = latest_articles[:5]
    weekly2_articles = ticker_articles

    tab_names = ("Lifestyle", "Travel", "Fashion", "Sports", "Technology")
    categories_by_name = {}
    for category in Category.objects.all():
        categories_by_name.setdefault(category.name.casefold(), []).append(category)

    category_tabs = []
    category_context = {}
    for name in tab_names:
        matches = categories_by_name.get(name.casefold(), [])
        category = matches[0] if len(matches) == 1 else None
        category_articles = (
            articles.filter(category=category).order_by(*ordering)
            if category else Article.objects.none()
        )
        category_context[f"{name.lower()}_articles"] = category_articles
        category_tabs.append({"name": name, "category": category, "articles": category_articles})

    return render(request, "index.html", {
        "trending_articles": trending_articles,
        "featured_trending_articles": trending_articles[:1],
        "bottom_trending_articles": trending_articles[1:4],
        "side_trending_articles": trending_articles[4:9],
        "all_published_articles": all_published_articles,
        "category_tabs": category_tabs,
        "recent_articles": recent_articles,
        "weekly_articles": weekly_articles,
        "weekly2_articles": weekly2_articles,
        "ticker_articles": ticker_articles,
        "youtube_videos": YOUTUBE_VIDEOS,
        **category_context,
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

