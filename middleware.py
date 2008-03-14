import re

LANG_MATCHER = re.compile(r'^([a-z]{2})/')

class LocaleMiddleware(object):
	def process_request(self, request):
		if LANG_MATCHER.search(request.path):
			request.session['django_language'] = request.path[0:2]
