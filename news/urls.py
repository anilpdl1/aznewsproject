from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("latest/", views.latest_news, name="latest_news"),
    path("search/", views.search, name="search"),
    path("newsletter/subscribe/", views.subscribe, name="subscribe"),
    path("category/", views.category_index, name="category_index"),
    path("category/<slug:slug>/", views.category, name="category"),
    path("article/<slug:slug>/", views.details, name="details"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("contact/categori.html", RedirectView.as_view(pattern_name="category_index", permanent=False)),
]
