from django.conf.urls import patterns, include, url
from .views import steamprofile_detail

urlpatterns = patterns('',
    url(r'^(?P<username>[\w\d_.-]+)/$', steamprofile_detail, name='steamprofile_detail'),
)
