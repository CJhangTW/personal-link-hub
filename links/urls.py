from django.urls import path

from . import views


app_name = "links"

urlpatterns = [
    path("healthz/", views.healthz, name="healthz"),
    path("", views.home, name="home"),
    path("r/<slug:slug>/", views.redirect_link, name="redirect-link"),
]
