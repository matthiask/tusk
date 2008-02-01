def subdict(dic, *args):
	return dict([(key, dic[key]) for key in args if key in dic])

def get_func(path):
	dot = path.rindex('.')
	return getattr(__import__(path[:dot], {}, {}, ['']), path[dot+1:])
