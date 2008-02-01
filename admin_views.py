# -*- coding: utf8 -*-

from django.shortcuts import get_object_or_404, render_to_response
from django import newforms as forms
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from django.utils import simplejson

from tusk import mptt_nsw_bridge
from tusk.forms import *
from tusk.models import Page, PageContent, PPCLink
from tusk.utils import subdict

@never_cache
@staff_member_required
def page_list(request):
	return render_to_response('admin/page_admin_list.html', {
		'title': 'Select page to change',
		}, context_instance=RequestContext(request))

@never_cache
@staff_member_required
def widget(request):
	if request.method == 'POST':
		mptt_nsw_bridge.process_store_tree(Page, request)
		return HttpResponse('OK')

	return HttpResponse(mptt_nsw_bridge.process_read_tree(Page,
		(('Page', '__unicode__'),
		('ID', 'pk'),
		('Template', 'template'),
		('State', 'state'),
		('Navigation', 'in_navigation'),
		('Commands', 'id'))),
		mimetype='text/plain')

def newcontentform(request, id, contenttype):
	page = get_object_or_404(Page, pk=int(id))
	content = PageContent.objects.create(content_type=contenttype, title='new content', state=PageContent.NEW)
	link = PPCLink.objects.create(page=page, content=content, block=page.get_template().get_blocks()[0])

	linkform = PPCLinkForm(page, instance=link)
	contentform = content.form()

	return HttpResponse(simplejson.dumps({
			'html': render_to_string('admin/pagecontentform.html', {
				'link': link,
				'content': content,
				'linkform': linkform,
				'contentform': contentform}),
			'javascript': contentform.javascript()
		}), mimetype='application/json')

def newlinkcontentform(request, pageid, contentid):
	page = get_object_or_404(Page, pk=pageid)
	content = get_object_or_404(PageContent, pk=contentid)

	link = PPCLink()
	link.block = page.get_template().get_blocks()[0]
	link.page = page
	link.content = content
	link.save()

	linkform = PPCLinkForm(page, instance=link)
	contentform = content.form()

	return HttpResponse(simplejson.dumps({
			'html': render_to_string('admin/pagecontentform.html', {
				'link': link,
				'content': content,
				'linkform': linkform,
				'contentform': contentform}),
			'javascript': contentform.javascript()
		}), mimetype='application/json')

def _get_link_and_content(post, keys, id):
	lk = 'ppc-%s-' % id
	ldata = dict([(str(k[len(lk):]), post.get(k)) for k in keys if k.startswith(lk)])
	ck = 'pc-%s-' % ldata['content']
	cdata = dict([(str(k[len(ck):]), post.get(k)) for k in keys if k.startswith(ck)])

	return (ldata, cdata)

@never_cache
@staff_member_required
def page_edit(request, id):

	PageContent.objects.filter(state=PageContent.NEW).delete()

	page = get_object_or_404(Page, pk=id)
	links = page.content_links.all()

	template = page.get_template()

	newpagecontentform = NewPageContentForm(prefix='npcf')

	if request.method == 'POST':
		pageform = PageForm(request.POST, instance=page)

		if pageform.is_valid():
			# TODO validation of content forms

			post = request.POST
			keys = post.keys()

			ppc_ids = [int(k[7:]) for k in keys if k.startswith('ppc-pk-')]

			if '_createcopy' in post:
				newpage = pageform.save(commit=False)
				newpage = Page(**subdict(newpage.__dict__, *Page.ADMIN_FIELDS))
				newpage.state = Page.DRAFT
				newpage.save()

				for id in ppc_ids:
					ldata, cdata = _get_link_and_content(post, keys, id)

					if 'remove' in ldata:
						continue

					content = PageContent(**subdict(cdata, *PageContent.ADMIN_FIELDS))
					content.save()

					link = PPCLink(**subdict(ldata, *PPCLink.ADMIN_FIELDS))
					link.page = newpage
					link.content = content
					link.save()

				request.user.message_set.create(
					message='Copy of %s successfully created. You are editing the copy now.' % (page))
				return HttpResponseRedirect('../%s/' % newpage.pk)

			pageform.save()
			request.user.message_set.create(message='Saved all changes.')

			for id in ppc_ids:
				try:
					link = PPCLink.objects.get(pk=id)
				except PPCLink.DoesNotExist:
					# oops. someone deleted it while we were editing...
					link = PPCLink()

				ldata, cdata = _get_link_and_content(post, keys, id)

				if 'remove' in ldata:
					if link.pk:
						link.delete()
					continue

				try:
					content = link.content
				except PageContent.DoesNotExist:
					content = PageContent()

				content.__dict__.update(subdict(cdata, *PageContent.ADMIN_FIELDS))
				content.save()

				link.__dict__.update(subdict(ldata, *PPCLink.ADMIN_FIELDS))

				link.page = page
				link.content = content
				link.save()

			if '_continue' in post:
				return HttpResponseRedirect('.')
			elif '_publish' in post:
				page.publish()

			return HttpResponseRedirect('../')

	else:
		pageform = PageForm(instance=page)
		contentforms = []

		for link in links:
			linkform = PPCLinkForm(page, instance=link)
			contentform = link.content.form()
			contentforms.append({
				'link': link,
				'content': link.content,
				'linkform': linkform,
				'contentform': contentform})

	return render_to_response('admin/page_admin_edit.html', {
		'title': 'Change page %s' % (page),
		'pageform': pageform,
		'contentforms': contentforms,
		'newpagecontentform': newpagecontentform,
		'page': page,
		}, context_instance=RequestContext(request))

'''
return HttpResponse('<div></div><script type="text/javascript">
window.open('{{ url }}');
window.location.href = '/admin/.../';
</script>')
'''
