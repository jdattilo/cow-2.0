from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required
from ae2 import views

urlpatterns = patterns('',
                       url(r'^pull$', views.pull, name="ae2pull"),
                       url(r'^run$', views.run, name="ae2run"),
                       url(r'^performtriage$', views.performtriage, name="performtriage"),
                       url(r'^changedirectory$', views.changedirectory, name='ae2directorychange'),
                       url(r'^copyenv$', views.copyenv, name='ae2copyenv'),
                       url(r'^copysuite$', views.copysuite, name='ae2copysuite'),
                       url(r'^newenv$', views.newenv, name='ae2newenv'),
                       url(r'^newsuite$', views.newsuite, name='ae2newsuite'),
                       url(r'^editfile$', views.editfile, name='ae2editfile'),
                       url(r'^halt$', views.halt_ae2, name='ae2halt'),
                       url(r'^envchange$', views.change_env, name='envchange'),
                       url(r'^automationsetup$', views.change_automation, name='automationsetup'),
                       url(r'^changecowmode$', views.change_cow_mode, name='change_cow_mode'),

                       url(r'^startbuildslave$', views.startbuildslave, name='startbuildslave'),
                       url(r'^stopbuildslave$', views.stopbuildslave, name='stopbuildslave'),
                       )
