from django.conf.urls.defaults import *

urlpatterns = patterns('tusk.views',
	url(r'^$', 'start'),
	url(r'^(?P<path>.*)/_preview/(?P<page_id>\d+)/', 'handler_preview'),
	url(r'^(?P<path>.*)/', 'handler'),
)
