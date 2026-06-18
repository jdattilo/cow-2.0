from django.conf.urls import patterns, url, include
from cowsystem import views

urlpatterns = patterns('',
                       url(r'^check$', views.systemcheck, name="checksystem"),
                       )
