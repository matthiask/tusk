# Create your views here.

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.admin.views.decorators import staff_member_required

from tusk.models import Page, PageContent, PPCLink
from tusk.utils import subdict

def start(request):
	return handler(request, 'home/')

def handler(request, path):
	page = Page.objects.page_for_path_or_404(path)
	template = page.get_template()

	return render_to_response(template.path, {
		'tusk': {
			'page': page,
			'blocks': page.get_blocks(),
		}}, context_instance=RequestContext(request))

@staff_member_required
def handler_preview(request, path, page_id):
	page = get_object_or_404(Page, pk=page_id)
	template = page.get_template()

	return render_to_response(template.path, {
		'tusk': {
			'page': page,
			'blocks': page.get_blocks(),
		}}, context_instance=RequestContext(request))
