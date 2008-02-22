from datetime import datetime
from django.db import models
from django.db.models import Q

class PageManager(models.Manager):
	def page_for_path(self, path):
		tokens = path.split('/')
		count = len(tokens)

		filters = {'%sisnull' % ('parent__' * count): True}

		for n, token in enumerate(tokens):
			filters['%sslug' % ('parent__' * (count-n-1))] = token

		try:
			return self.published().filter(**filters)[0]
		except IndexError:
			raise self.model.DoesNotExist

	def page_for_path_or_404(self, path):
		try:
			return self.page_for_path(path)
		except self.model.DoesNotExist:
			from django.http import Http404
			raise Http404

	def published(self):
		return self.filter(
			Q(state=self.model.PUBLISHED),
			Q(start_publish_date__lte=datetime.now()) | Q(start_publish_date__isnull=True),
			Q(end_publish_date__gte=datetime.now()) | Q(end_publish_date__isnull=True))

	def in_navigation(self):
		return self.published().filter(in_navigation=True)

	def toplevel_navigation(self):
		return self.in_navigation().filter(parent__isnull=True)

class PageContentManager(models.Manager):
	def published(self):
		return self.filter(state=self.model.PUBLISHED)
