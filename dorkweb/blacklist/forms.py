from django import forms


class BlacklistForm(forms.Form):
    regex = forms.CharField(label='regex', required=False)
    ip = forms.CharField(label='ip', required=False)
    host = forms.CharField(label='host', required=False)
