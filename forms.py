from django import newforms as forms
from django.conf import settings
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe

from tusk.models import Page, PageContent, PPCLink

class DateTimeWidget(forms.widgets.SplitDateTimeWidget):
	def render(self, name, value, attrs=None):
		self.widgets[0].attrs.update({'class': 'vDateField'})
		self.widgets[1].attrs.update({'class': 'vTimeField'})
		return super(DateTimeWidget, self).render(name, value, attrs)

class DateWidget(forms.widgets.Input):
	input_type = 'text' # Subclasses must define this.

	def render(self, name, value, attrs=None):
		attrs.update({'class': 'vDateField'})
		return super(DateWidget, self).render(name, value, attrs)

class TuskModelForm(forms.ModelForm):
	def as_div(self):
		return self._html_output(u'<div class="form-row">%(label)s %(errors)s %(field)s %(help_text)s</div>', u'%s', '</div>', u' %s', False)

class PageForm(TuskModelForm):
	start_publish_date = forms.SplitDateTimeField(widget=DateTimeWidget, required=False)
	end_publish_date = forms.SplitDateTimeField(widget=DateTimeWidget, required=False)

	class Meta:
		model = Page

class NewPageContentForm(forms.Form):
	content_type = forms.ChoiceField(label='Type for new page content')
	pagecontent = forms.ChoiceField(label='Use page content')

	def __init__(self, *args, **kwargs):
		super(NewPageContentForm, self).__init__(*args, **kwargs)
		self.fields['content_type'].choices = (('', '-- select --'),) + PageContent.CONTENT_TYPE_CHOICES
		self.fields['pagecontent'].choices = [('', '-- select --'),] + [(obj.pk, unicode(obj)) for obj in PageContent.objects.filter(state__in=(PageContent.STATES))]

	def as_div(self):
		return self._html_output(u'<div class="form-row">%(label)s %(errors)s %(field)s %(help_text)s</div>', u'%s', '</div>', u' %s', False)

class PPCLinkForm(TuskModelForm):
	page = forms.IntegerField(widget=forms.HiddenInput)
	content = forms.IntegerField(widget=forms.HiddenInput)
	block = forms.ChoiceField()
	remove = forms.BooleanField()

	def __init__(self, page, *args, **kwargs):
		super(PPCLinkForm, self).__init__(*args, **kwargs)

		blocks = page.get_template().get_blocks()
		self.fields['block'].choices = zip(blocks, blocks)

		self.fields.insert(0, 'remove', self.fields['remove'])

	class Meta:
		model = PPCLink

	def render(self):
		return mark_safe(u''.join([self.as_div(),
			'<input type="hidden" name="ppc-pk-%s" value="1" />' % self.instance.pk]))

	def add_prefix(self, field_name):
		return self.prefix and ('ppc-%s-%s-%s' % (self.prefix, self.instance.pk, field_name)) or \
			'ppc-%s-%s' % (self.instance.pk, field_name)

class PageContentForm(TuskModelForm):
	content_type = forms.CharField(widget=forms.HiddenInput)

	class Meta:
		model = PageContent

	def add_prefix(self, field_name):
		return self.prefix and ('pc-%s-%s-%s' % (self.prefix, self.instance.pk, field_name)) or \
			'pc-%s-%s' % (self.instance.pk, field_name)

	def render(self):
		return mark_safe(''.join([self.as_div(),
			'<input type="hidden" name="pc-pk-%s" value="1" />' % self.instance.pk]))

	def javascript(self):
		return u''

class TextPageContentForm(PageContentForm):
	meta = forms.CharField(widget=forms.HiddenInput)

	def __init__(self, *args, **kwargs):
		kwargs['instance'].meta = 'richtext'
		super(TextPageContentForm, self).__init__(*args, **kwargs)

	def javascript(self):
		return mark_safe(u'tinyMCE.execCommand("mceAddControl", true, "id_%s");' % self.add_prefix('content'))

class FunctionPageContentForm(PageContentForm):
	meta = forms.CharField(widget=forms.HiddenInput)
	content = forms.CharField(label='Function', widget=forms.TextInput())

class TemplatePageContentForm(PageContentForm):
	meta = forms.CharField(widget=forms.HiddenInput)
	content = forms.CharField(label='Template', widget=forms.TextInput())
