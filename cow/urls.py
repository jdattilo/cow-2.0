from django.conf.urls import include, url
from django.contrib import admin
from dashboard.views import index, logview, buildbot_json_simulator, cow_update, cow_version, cow_update_external, activityLogs, runLogs
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Examples:
    # url(r'^$', 'cow.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', index, name='dashboard'),
    url(r'^activities$', activityLogs, name='activities'),
    url(r'^runs$', runLogs, name='runLogs'),
    url(r'^builds/-1$', buildbot_json_simulator, name='buildbot_json_simulator'),
    url(r'^updatecow$', cow_update, name='cow_update'),
    url(r'^updatecow_external$', cow_update_external, name='cow_update_external'),
    url(r'^cowversion$', cow_version, name='cow_version'),
    url(
        r'^logview/(?P<logname>.*)/(?P<build_number>[0-9]+)$',
        logview,
        name='logview'),
    url(r'^system/', include('cowsystem.urls', namespace='cowsystem')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('accounts.urls', namespace='accounts')),
    url(r'^ae2/', include('ae2.urls', namespace='ae2')),
    url(r'^bamboo/', include('bamboo.urls', namespace='bamboo')),
    url(r'^enqueued/', include('enqueued.urls', namespace='enqueued')),
    url(r'^cluster/', include('cluster.urls', namespace='cluster')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
