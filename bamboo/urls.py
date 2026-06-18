from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required
from bamboo import views

urlpatterns = patterns(
    '', url(r'^update$', views.changesettings, name="bamboosettingschange"), )
