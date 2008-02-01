from django.conf.urls.defaults import *
from django.contrib.admin.views.main import change_stage, history, delete_stage
from django.views.generic.simple import redirect_to

urlpatterns = patterns('',
	url(r'tusk/page/$', 'tusk.admin_views.page_list'),
	url(r'tusk/page/widget/$', 'tusk.admin_views.widget'),
	url(r'tusk/page/newcontentform/(?P<id>\d+)/(?P<contenttype>\w+)/$', 'tusk.admin_views.newcontentform'),
	url(r'tusk/page/newlinkcontentform/(?P<pageid>\d+)/(?P<contentid>\d+)/$', 'tusk.admin_views.newlinkcontentform'),
	url(r'tusk/page/(?P<id>\d+)/$', 'tusk.admin_views.page_edit'),
)
