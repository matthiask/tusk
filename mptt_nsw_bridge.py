from django.db import connection
from django.utils.encoding import smart_unicode
from django.utils import simplejson

__all__ = ['process_store_tree', 'process_read_tree']

def left_right(structure, counter=1, parent='NULL', level=0):
	# id tree_id parent left right
	ret = []
	for elem in structure:
		item = [left_right.tree, parent, counter, 0, level, int(elem['id'])]
		children = elem.get('children')
		counter += 1

		if children:
			arr, counter = left_right(children, counter, int(elem['id']), level+1)
			ret += arr

		item[3] = counter
		counter += 1
		ret.append(item)

		if parent == 'NULL':
			left_right.tree += 1
			counter = 1

	return ret, counter

def store_tree(cls, tree):
	left_right.tree = 1
	mptt_tree, counter = left_right(tree)
	cursor = connection.cursor()

	for elem in mptt_tree:
		sql = "UPDATE %s SET %s=%%s, %s_id=%%s, %s=%%s, %s=%%s, %s=%%s WHERE %s=%%s" % (
			cls._meta.db_table,
			cls._meta.tree_id_attr,
			cls._meta.parent_attr,
			cls._meta.left_attr,
			cls._meta.right_attr,
			cls._meta.level_attr,
			cls._meta.pk.column)

		cursor.execute(sql % tuple(elem))

def process_store_tree(cls, request):
	structure = simplejson.loads(request.POST.get('nested-sortable-widget'))
	store_tree(cls, structure.get('items'))

def process_read_tree(cls, fields):
	resp = {}

	resp['requestFirstIndex'] = resp['firstIndex'] = 0
	resp['count'] = resp['totalCount'] = cls.objects.count()
	resp['columns'] = [item[0] for item in fields]
	resp['items'] = return_array(cls.tree.root_nodes(), [item[1] for item in fields])

	return simplejson.dumps(resp)

def __get_dynamic_attr(o, attname, obj=None, default=None):
	try:
		attr = getattr(o, attname)
	except AttributeError:
		return default
	if callable(attr):
		# Check func_code.co_argcount rather than try/excepting the
		# function and catching the TypeError, because something inside
		# the function may raise the TypeError. This technique is more
		# accurate.
		if hasattr(attr, 'func_code'):
			argcount = attr.func_code.co_argcount
		else:
			argcount = attr.__call__.func_code.co_argcount
		if argcount == 2: # one argument is 'self'
			return attr(obj)
		else:
			return attr()
	return attr

def return_array(struct, fieldlist):
	ret = []
	for elem in struct:
		dic = {}
		dic['id'] = elem.id
		dic['info'] = [smart_unicode(__get_dynamic_attr(elem, field, elem)) for field in fieldlist]

		children = elem.get_children()

		if not elem.is_leaf_node():
			dic['children'] = return_array(elem.get_children(), fieldlist)

		ret.append(dic)

	return ret
