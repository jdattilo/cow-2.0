from django.conf.urls import patterns, url, include
from enqueued import views
from rest_framework.urlpatterns import format_suffix_patterns

# API endpoints
urlpatterns = format_suffix_patterns([
    url(r'^rest$', views.api_root),
])

# Login and logout views for the browsable API
urlpatterns += [url(r'^runnext$',
                    views.runnext,
                    name="enqueuedjob"),
                url(r'^runae2$',
                    views.runae2,
                    name="enqueuedae2job"),
                url(r'^api-auth/$',
                    include('rest_framework.urls',
                            namespace='rest_framework')),
                ]
