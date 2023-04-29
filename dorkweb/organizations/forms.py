from django import forms
from .models import Organization, Domain

DomainFormSet = forms.models.inlineformset_factory(Organization, Domain, fields = ['name'], extra=0)

