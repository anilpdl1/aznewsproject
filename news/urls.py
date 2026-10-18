from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('latest/', views.latest_news, name='latest_news'),
    path('category/<slug:slug>/', views.category, name='category'),
    path('article/<slug:slug>/', views.details, name='details'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
