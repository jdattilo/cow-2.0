from django.conf.urls import patterns, url, include
from accounts import views

urlpatterns = patterns('',
                       url(r'^login/$', views.login_user, name='login'),
                       url(r'^logout/$', views.logout_user, name='logout'),
                       )
