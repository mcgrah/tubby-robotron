import datetime
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from robotron_app.models import Actor

from dal import autocomplete


class UploadCSVForm(forms.Form):
    file = forms.FileField()


class AddBatchForm(forms.Form):
    new_batch_name = forms.CharField(min_length=1, required=True, label='Name')
    # project assigned automatically form project detail page
    # new_batch_project =
    new_batch_start_date = forms.DateField(initial=datetime.date.today, required=False, label='Start Date')
    new_batch_deadline = forms.DateField(required=False, label='Deadline')
    new_batch_files_count = forms.IntegerField(min_value=0, initial=0,  required=False, label='Files')
    new_batch_word_count = forms.IntegerField(min_value=0, initial=0, required=False, label='Words')
    new_batch_char_count = forms.IntegerField(min_value=0, initial=0, required=False, label='Characters')

    # deadline should be after start_date
    def clean_new_batch_deadline(self):
        data = self.cleaned_data['new_batch_deadline']
        if data < self.cleaned_data['new_batch_start_date']:
            raise ValidationError(_('Invalid date - deadline set before start_date'))

        return data


class AddCharacterForm(forms.Form):
    new_char_name = forms.CharField(min_length=1, required=True, label='Name')
    # batch assigned automatically from batch detail page
    new_char_files_count = forms.IntegerField(min_value=0, initial=0,  required=False, label='Files')
    new_char_delivery_date = forms.DateField(required=False, label='Delivery Date')
    new_char_delivery_time = forms.DateField(required=False, label='Delivery Time')
    # actor needs to be chosen or created from scratch if not found
    new_char_actor = forms.ModelChoiceField(
        queryset=Actor.objects.all(),
        widget=autocomplete.ModelSelect2(url='actor-autocomplete'),
        label='Actor',
        required=False
    )
