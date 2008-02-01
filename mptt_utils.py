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
		dic['info'] = [__get_dynamic_attr(elem, field, elem) for field in fieldlist]

		children = elem.get_children()

		if not elem.is_leaf_node():
			dic['children'] = _return_array(elem.get_children(), fieldlist)

		ret.append(dic)

	return ret

def left_right(structure, counter=1, parent='NULL', level=0):
	# id tree_id parent left right
	ret = []
	for elem in structure:
		item = [_left_right.tree, parent, counter, 0, level, int(elem['id'])]

		children = elem.get('children')

		counter += 1

		if children:
			arr, counter = _left_right(children, counter, int(elem['id']), level+1)
			ret += arr

		item[3] = counter

		counter += 1

		ret.append(item)

		if parent=='NULL':
			_left_right.tree += 1
			counter = 1

	return ret, counter
