from datetime import datetime

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
import mptt

from tusk.managers import PageManager, PageContentManager
from tusk.utils import subdict, get_func

class Template(models.Model):
	title = models.CharField(max_length=200)
	path = models.CharField(max_length=200)
	blocks = models.CharField(max_length=200)

	created = models.DateTimeField(editable=False, auto_now_add=True)
	last_modified = models.DateTimeField(editable=False, auto_now=True)

	class Admin:
		list_display = ('title', 'path', 'blocks')

	class Meta:
		ordering = ['title']

	def get_blocks(self):
		return self.blocks.split(',')

	def __unicode__(self):
		return u'%s (%s)' % (self.title, self.path)

DEFAULT_TEMPLATE = Template(title='<Default Template>', path='base.html', blocks='content')

class Page(models.Model):
	PUBLISHED = 'published'
	DRAFT = 'draft'
	ARCHIVED = 'archived'
	STATE_CHOICES = ((DRAFT, DRAFT), (PUBLISHED, PUBLISHED), (ARCHIVED, ARCHIVED))

	ADMIN_FIELDS = ('title', 'slug', 'parent_id', 'override_url', 'template_id',
		'in_navigation', 'start_publish_date', 'end_publish_date', 'meta')

	title = models.CharField(max_length=200)
	slug = models.SlugField(max_length=50, prepopulate_from=('title',))
	parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

	override_url = models.CharField(max_length=200, blank=True, null=True)
	template = models.ForeignKey(Template, blank=True, null=True)

	state = models.CharField(max_length=20, choices=STATE_CHOICES, default=DRAFT, db_index=True)
	in_navigation = models.BooleanField(default=True)
	start_publish_date = models.DateTimeField(null=True, blank=True)
	end_publish_date = models.DateTimeField(null=True, blank=True)

	created = models.DateTimeField(editable=False, auto_now_add=True)
	last_modified = models.DateTimeField(editable=False, auto_now=True)

	author = models.ForeignKey(User, editable=False, related_name='authored_pages')

	meta = models.TextField(blank=True)

	class Admin:
		pass

	class Meta:
		ordering = ['lft']

	objects = PageManager()

	def save(self):
		if not self.author_id:
			from feinheit.middleware import get_current_user
			self.author = get_current_user()

		super(Page, self).save()

	def __unicode__(self):
		return "%s (%s)" % (self.title, self.get_absolute_url())

	def get_blocks(self):
		links = self.content_links.select_related().filter(
			content__state=PageContent.PUBLISHED)

		return dict([(link.block, link) for link in links])

	def _get_attr_from_self_or_ancestors(self, attr):
		v = getattr(self, attr)
		if v is not None:
			return v

		ancestors = self.get_ancestors(True)

		for ancestor in ancestors:
			v = getattr(ancestor, attr)
			if v is not None:
				return v

	def get_template(self):
		template_id = self._get_attr_from_self_or_ancestors('template_id')

		if template_id:
			return Template.objects.get(pk=template_id)

		return DEFAULT_TEMPLATE

	def get_absolute_url(self):
		if self.override_url != '':
			return self.override_url
		if self.is_root_node():
			return u'/%s/' % (self.slug)
		else:
			return u'/%s/%s/' % ('/'.join([page.slug for page in self.get_ancestors()]), self.slug)

	def save_copy(self):
		page = Page(**subdict(self.__dict__, *Page.ADMIN_FIELDS))
		page.state = Page.DRAFT
		page.predecessor = self
		page.save()

		links = self.content_links.select_related()
		for link in links:
			content = PageContent(**subdict(link.content.__dict__, *PageContent.ADMIN_FIELDS))
			content.save()

			ppclink = PPCLink(**subdict(link.__dict__, *PPCLink.ADMIN_FIELDS))
			ppclink.page = page
			ppclink.content = content
			ppclink.save()

		return page

	def publish(self):
		try:
			if self.parent is None:
				page = Page.objects.filter(parent__isnull=True, state=Page.PUBLISHED, slug=self.slug)[0]
			else:
				page = self.parent.children.filter(state=Page.PUBLISHED, slug=self.slug)[0]
			page.state = Page.ARCHIVED
			page.save()

			self.save()

			for child in page.get_children():
				#child.move_to(self, position='last-child')
				child.parent = self
				child.save()

		except IndexError:
			pass

		self.state = Page.PUBLISHED
		self.save()

mptt.register(Page)

class InvalidContentTypeException(Exception):
	pass

class PageContent(models.Model):
	TEXT = 'text'
	TEMPLATE = 'template'
	FUNCTION = 'function'
	CONTENT_TYPE_CHOICES = ((TEXT, TEXT), (TEMPLATE, TEMPLATE), (FUNCTION, FUNCTION))

	PUBLISHED = 'published'
	DRAFT = 'draft'
	NEW = 'new' # not included in choices
	STATES = (DRAFT, PUBLISHED)
	STATE_CHOICES = ((DRAFT, DRAFT), (PUBLISHED, PUBLISHED))

	ADMIN_FIELDS = ('content_type', 'state', 'title', 'content', 'meta')

	content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default=TEXT)

	state = models.CharField(max_length=20, choices=STATE_CHOICES, default=DRAFT, db_index=True)
	title = models.CharField(max_length=200)
	content = models.TextField(blank=True)
	meta = models.TextField(blank=True)

	created = models.DateTimeField(editable=False, auto_now_add=True)
	last_modified = models.DateTimeField(editable=False, auto_now=True)

	author = models.ForeignKey(User, editable=False, related_name='authored_contents')

	class Admin:
		pass

	def __unicode__(self):
		return u'%s (created %s by %s, last modified %s, %s)' % (
			self.title,
			self.created.strftime('%d.%m.%Y %H:%M'),
			self.author,
			self.last_modified.strftime('%d.%m.%Y %H:%M'),
			self.state)

	def _render(self, link):
		if self.content_type == self.TEXT:
			return self.content
		elif self.content_type == self.TEMPLATE:
			from django.template import render_to_string
			return render_to_string(self.content)
		elif self.content_type == self.FUNCTION:
			try:
				func = get_func(self.content)
			except (ImportError, AttributeError, ValueError), e:
				raise StandardError('Could not import %s' % self.content)
			return func(link)
		else:
			raise InvalidContentTypeException

	def form(self, *args, **kwargs):
		from tusk import forms

		kwargs.setdefault('instance', self)

		cls = forms.PageContentForm

		if self.content_type == self.TEXT:
			cls = forms.TextPageContentForm
		elif self.content_type == self.TEMPLATE:
			cls = forms.TemplatePageContentForm
		elif self.content_type == self.FUNCTION:
			cls = forms.FunctionPageContentForm

		return cls(*args, **kwargs)

class PPCLink(models.Model):
	ADMIN_FIELDS = ('block',)

	page = models.ForeignKey(Page, related_name='content_links')
	content = models.ForeignKey(PageContent, related_name='page_links')
	block = models.CharField(max_length=20) # TODO choices

	created = models.DateTimeField(editable=False, auto_now_add=True)
	last_modified = models.DateTimeField(editable=False, auto_now=True)

	def __unicode__(self):
		return u'%s: %s' % (self.block, self.content)

	class Meta:
		ordering = []

	def title(self):
		return self.content.title

	def render(self):
		return self.content._render(self)

	def meta(self):
		return self.content.meta
