from django.conf.urls import url, include
from django.contrib import admin
from endpoint import views

urlpatterns = [
    url(r'^update', views.update)

]
