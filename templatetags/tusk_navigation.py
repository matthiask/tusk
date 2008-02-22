from django import template
from tusk.models import Page
from tusk.templatetags.utils import *

register = template.Library()

class NavigationNode(SimpleAssignmentNodeWithVarAndArgs):
	def what(self, instance, args):
		level = int(args.get('level', 1))

		if level <= 1:
			return Page.objects.toplevel_navigation()

		if instance.level+2 == level:
			return instance.children.in_navigation()

		try:
			return instance.get_ancestors()[level-2].children.in_navigation()
		except IndexError:
			return []
register.tag('tusk_navigation', do_simple_assignment_node_with_var_and_args_helper(NavigationNode))

class SubnavigationNode(SimpleAssignmentNodeWithVar):
	def what(self, page):
		return page.children.in_navigation().all()
register.tag('tusk_subnavigation', do_simple_assignment_node_with_var_helper(SubnavigationNode))

class BreadcrumbsNode(SimpleAssignmentNodeWithVar):
	def what(self, page):
		return page.get_ancestors()
register.tag('tusk_breadcrumbs', do_simple_assignment_node_with_var_helper(BreadcrumbsNode))

class HierarchyNode(SimpleAssignmentNode):
	def hierarchy(self, page):
		if page.is_leaf_node():
			return None

		return [(p, self.hierarchy(p)) for p in page.children.in_navigation().all()]

	def what(self):
		return Page.objects.toplevel_navigation()
register.tag('tusk_hierarchy', do_simple_assignment_node_helper(HierarchyNode))

class LinkNode(SimpleNodeWithVarAndArgs):
	def what(self, page, args):
		level = int(args.get('level', 1))

		if page.level+1 == level:
			return page.get_absolute_url()
		elif page.level+1 < level:
			return '#'

		try:
			return page.get_ancestors()[level-1].get_absolute_url()
		except IndexError:
			return '#'
register.tag('tusk_link', do_simple_node_with_var_and_args_helper(LinkNode))

@register.simple_tag
def sql_queries():
	from django.db import connection
	html = []
	html.append('<ul><li>')
	html.append('</li><li>'.join('%s (%s)' % (item['sql'], item['time']) for item in connection.queries))
	html.append('</li></ul>')

	html.append('%s queries, %s' % (
		len(connection.queries),
		reduce(lambda x,y: x+y, [float(item['time']) for item in connection.queries])
		))

	return ''.join(html)
