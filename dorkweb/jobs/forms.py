from django import forms
from .models import Job
from organizations.models import Organization, Domain


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['task', 'organization', 'domain']
        widgets = {'organization': forms.Select(attrs = {'onchange' : "load_domains();"}),
                   'task': forms.Select(attrs = {'onchange' : "hide_domains();"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['organization'].queryset = Organization.objects.filter(enabled=True)
        self.fields['domain'].queryset = Domain.objects.none()

        if 'organization' in self.data:
            self.fields['domain'].queryset = Domain.objects.filter(organization=int(self.data.get('organization')))
        
