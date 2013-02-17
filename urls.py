from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.conf.urls.static import static

from appdisk.views import *

urlpatterns = patterns('',
    url(r'^$', files, name='appdisk_home'),
    url(r'^files/$', files,  name='appdisk_files'),
    url(r'^upload/$', upload, name='appdisk_upload'),
    url(r'^remove/$', remove, name='appdisk_remove'),
    url(r'^newdir/$', newdir, name='appdisk_newdir'),
    url(r'^subdir/$', subdir, name='appdisk_subdir'),
    url(r'^test/', test, name='test'),
)