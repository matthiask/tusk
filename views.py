from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.admin.views.decorators import staff_member_required

from tusk.models import Page

def start(request):
	return handler(request, 'home/')

def slash_check(fn):
	def _func(request, *args, **kwargs):
		if request.path[-1:] != '/':
			return HttpResponsePermanentRedirect('%s/' % request.path)

		return fn(request, *args, **kwargs)

	return _func

def _handle_meta(meta):
	for line in meta.splitlines():
		cmd, arg = line.split()

		if cmd == 'redirect:':
			return HttpResponseRedirect(arg)

def _handle_page(request, page):
	if page.meta:
		ret = _handle_meta(page.meta)

		if ret:
			return ret

	template = page.get_template()

	return render_to_response(template.path, {
		'tusk': {
			'page': page,
			'blocks': page.get_blocks(),
		}}, context_instance=RequestContext(request))

def handler(request, path):
	return _handle_page(request, Page.objects.page_for_path_or_404(path))

@staff_member_required
def handler_preview(request, path, page_id):
	return _handle_page(request, get_object_or_404(Page, pk=page_id))
