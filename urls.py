from django.conf.urls.defaults import *
from django.contrib.admin.views.main import change_stage, history, delete_stage
from django.views.generic.simple import redirect_to

urlpatterns = patterns('tusk.views',
	url(r'^$', 'start'),
	url(r'^(?P<path>.*)/_preview/(?P<page_id>\d+)/', 'handler_preview'),
	url(r'^(?P<path>.*)/', 'handler'),
)
