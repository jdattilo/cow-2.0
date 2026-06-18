from django.conf.urls import patterns, url, include
from cluster import views

urlpatterns = patterns(
    '', url(
        r'^check$', views.check, name="checkcluster"), url(
            r'^checkfldc$', views.checkfldc, name="checkfldc"), url(
                r'^cleancluster$', views.clean_cluster, name="clean_cluster"), url(
                    r'^collectcluster$', views.collect_cluster, name="collect_cluster"), )
