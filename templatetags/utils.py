'''
I really hate repeating myself. These are helpers that avoid typing the
whole thing over and over when implementing additional template tags

They help implementing tags of the form

{% tag as var_name %} (SimpleAssignmentNode)
and
{% tag of template_var as var_name %} (SimpleAssignmentNodeWithVar)
'''

from django import template

def _parse_args(argstr):
	try:
		args = {}
		for token in argstr.split(','):
			k, v = token.split('=')
			args[k] = v

		return args

	except TypeError:
		raise template.TemplateSyntaxError('Malformed arguments')

def do_simple_node_with_var_and_args_helper(cls):
	def _func(parser, token):
		try:
			tag_name, of_, in_var_name, args = token.contents.split()
		except ValueError:
			raise template.TemplateSyntaxError

		return cls(tag_name, in_var_name, args)

	return _func

class SimpleNodeWithVarAndArgs(template.Node):
	def __init__(self, tag_name, in_var_name, args):
		self.tag_name = tag_name
		self.in_var = template.Variable(in_var_name)
		self.args = args

	def render(self, context):
		try:
			instance = self.in_var.resolve(context)
		except template.VariableDoesNotExist:
			return ''

		return self.what(instance, _parse_args(self.args))

def do_simple_node_with_var_helper(cls):
	def _func(parser, token):
		try:
			tag_name, of_, in_var_name = token.contents.split()
		except ValueError:
			raise template.TemplateSyntaxError

		return cls(tag_name, in_var_name)

	return _func

class SimpleNodeWithVar(template.Node):
	def __init__(self, tag_name, in_var_name):
		self.tag_name = tag_name
		self.in_var = template.Variable(in_var_name)

	def render(self, context):
		try:
			instance = self.in_var.resolve(context)
		except template.VariableDoesNotExist:
			return ''

		return self.what(instance)

def do_simple_assignment_node_helper(cls):
	def _func(parser, token):
		try:
			tag_name, as_, var_name = token.contents.split()
		except ValueError:
			raise template.TemplateSyntaxError

		return cls(tag_name, var_name)

	return _func

class SimpleAssignmentNode(template.Node):
	def __init__(self, tag_name, var_name):
		self.tag_name = tag_name
		self.var_name = var_name

	def render(self, context):
		context[self.var_name] = self.what()
		return ''

def do_simple_assignment_node_with_var_helper(cls):
	def _func(parser, token):
		try:
			tag_name, of_, in_var_name, as_, var_name = token.contents.split()
		except ValueError:
			raise template.TemplateSyntaxError

		return cls(tag_name, in_var_name, var_name)

	return _func

class SimpleAssignmentNodeWithVar(template.Node):
	def __init__(self, tag_name, in_var_name, var_name):
		self.tag_name = tag_name
		self.in_var = template.Variable(in_var_name)
		self.var_name = var_name

	def render(self, context):
		try:
			instance = self.in_var.resolve(context)
		except template.VariableDoesNotExist:
			context[self.var_name] = []
			return ''

		context[self.var_name] = self.what(instance)
		return ''

def do_simple_assignment_node_with_var_and_args_helper(cls):
	def _func(parser, token):
		try:
			tag_name, of_, in_var_name, as_, var_name, args = token.contents.split()
		except ValueError:
			raise template.TemplateSyntaxError

		return cls(tag_name, in_var_name, var_name, args)

	return _func

class SimpleAssignmentNodeWithVarAndArgs(template.Node):
	def __init__(self, tag_name, in_var_name, var_name, args):
		self.tag_name = tag_name
		self.in_var = template.Variable(in_var_name)
		self.var_name = var_name
		self.args = args

	def render(self, context):
		try:
			instance = self.in_var.resolve(context)
		except template.VariableDoesNotExist:
			context[self.var_name] = []
			return ''

		context[self.var_name] = self.what(instance, _parse_args(self.args))

		return ''
