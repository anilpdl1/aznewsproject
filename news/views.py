from django.core.paginator import Paginator
from django.db.models import F, Q
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from .models import Article, Category, Comment, ContentPage, HomepageVideo, Subscriber
from .forms import CommentForm, ContactForm, SubscriberForm
from .context_processors import get_global_categories
def published_articles():
    return Article.objects.filter(is_published=True).select_related(
        "author", "category"
    )


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

    categories = get_global_categories(request)
    category_tabs = []
    category_context = {}
    for category in categories:
        category_articles = articles.filter(category=category).order_by(*ordering)
        category_context[f"{category.slug.replace('-', '_')}_articles"] = category_articles
        category_tabs.append(
            {"name": category.name, "category": category, "articles": category_articles}
        )

    return render(
        request,
        "index.html",
        {
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
            "youtube_videos": HomepageVideo.objects.filter(is_active=True),
            **category_context,
        },
    )


def category(request, slug):
    selected_category = get_object_or_404(Category, slug=slug)
    article_list = (
        published_articles()
        .filter(category=selected_category)
        .order_by("-created_at", "-pk")
    )
    page_obj = Paginator(article_list, 10).get_page(request.GET.get("page"))
    return render(
        request,
        "categori.html",
        {
            "category": selected_category,
            "page_obj": page_obj,
            "articles": page_obj.object_list,
        },
    )


def category_index(request):
    article_list = published_articles().order_by("-created_at", "-pk")
    page_obj = Paginator(article_list, 10).get_page(request.GET.get("page"))
    return render(
        request,
        "categori.html",
        {
            "category": None, "page_obj": page_obj, "articles": page_obj.object_list,
            "show_whats_new": True,
            "all_published_articles": article_list,
            "category_tabs": [
                {"name": item.name, "articles": published_articles().filter(category=item).order_by("-created_at", "-pk")}
                for item in get_global_categories(request)
            ],
        },
    )


def latest_news(request):
    article_list = published_articles().order_by("-created_at", "-pk")
    page_obj = Paginator(article_list, 10).get_page(request.GET.get("page"))
    return render(
        request,
        "latest_news.html",
        {"page_obj": page_obj, "articles": page_obj.object_list},
    )


def details(request, slug):
    article = get_object_or_404(published_articles(), slug=slug)
    Article.objects.filter(pk=article.pk).update(views_count=F("views_count") + 1)
    article.refresh_from_db(fields=("views_count",))
    related_articles = (
        published_articles()
        .filter(category=article.category)
        .exclude(pk=article.pk)
        .order_by("-created_at", "-pk")[:4]
    )
    comment_form = CommentForm(request.POST or None)
    if request.method == "POST":
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.article = article
            comment.is_approved = False
            comment.save()
            messages.success(request, "Your comment was submitted and is awaiting approval.")
            return HttpResponseRedirect(reverse("details", kwargs={"slug": article.slug}))
        messages.error(request, "Please correct the errors in the comment form.")
    comments = article.comments.filter(is_approved=True)
    return render(request, "single-blog.html", {
        "article": article, "related_articles": related_articles,
        "comments": comments, "comment_form": comment_form,
    })


def about(request):
    page = get_object_or_404(ContentPage, slug="about", is_published=True)
    return render(request, "about.html", {"page": page})


def search(request):
    query = request.GET.get("q", "").strip()
    results = published_articles()
    if query:
        results = results.filter(Q(title__icontains=query) | Q(content__icontains=query)).distinct()
    else:
        results = results.none()
    results = results.order_by("-created_at", "-pk")
    page_obj = Paginator(results, 10).get_page(request.GET.get("page"))
    return render(request, "search_results.html", {
        "query": query, "page_obj": page_obj, "articles": page_obj.object_list,
        "result_count": results.count(),
    })


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        contact_message = form.save()
        messages.success(request, "Your message has been sent successfully.")
        recipient = getattr(settings, "CONTACT_NOTIFICATION_EMAIL", "")
        if recipient:
            try:
                send_mail(
                    f"Contact form: {contact_message.subject}",
                    f"From: {contact_message.name} <{contact_message.email}>\n\n{contact_message.message}",
                    settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=True,
                )
            except Exception:
                pass
        return HttpResponseRedirect(reverse("contact"))
    if request.method == "POST":
        messages.error(request, "Please correct the errors in the contact form.")
    return render(request, "contact.html", {"form": form})


def subscribe(request):
    if request.method == "POST":
        form = SubscriberForm(request.POST)
        next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("home")
        if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            next_url = reverse("home")
        if form.is_valid():
            email = form.cleaned_data["email"]
            subscriber, created = Subscriber.objects.get_or_create(email=email)
            if not subscriber.is_active:
                subscriber.is_active = True
                subscriber.save(update_fields=["is_active"])
                created = True
            if created:
                messages.success(request, "Thanks for subscribing to the newsletter.")
            else:
                messages.info(request, "This email is already subscribed.")
        else:
            messages.error(request, "Please enter a valid email address.")
        return HttpResponseRedirect(next_url)
    return HttpResponseRedirect(reverse("home"))
