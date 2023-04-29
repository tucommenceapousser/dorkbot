from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.forms import CharField, Textarea
from .models import Organization, Domain
from .forms import DomainFormSet
import re

class OrganizationListView(generic.ListView):
    model = Organization

    def get_context_data(self, **kwargs):
        context = super(OrganizationListView, self).get_context_data(**kwargs)
        context['enabled_organization_list'] = context['organization_list'].filter(enabled=True)
        context['disabled_organization_list'] = context['organization_list'].filter(enabled=False)
        return context


class OrganizationDetailView(generic.DetailView):
    model = Organization


class OrganizationCreateView(generic.CreateView):
    model = Organization
    success_url = '/organizations/'
    fields = ['name']

    def get_context_data(self, **kwargs):
        context = super(OrganizationCreateView, self).get_context_data(**kwargs)
        context['form'].fields['domains'] = CharField(widget=Textarea, required=False)
        if self.request.POST:
            context['domain_formset'] = DomainFormSet(self.request.POST)
        else:
            context['domain_formset'] = DomainFormSet()
        return context

    def form_valid(self, form):
        domains = form.data['domains']
        domain_set = set()
        for domain in re.split('[\s,]+', domains):
            if domain:
                domain_set.add(domain)
        if not domain_set:
            domain_set.add(form.cleaned_data['name'])

        context = self.get_context_data(form = form)
        prefix = context['domain_formset'].prefix
        post = self.request.POST.copy()
        post[prefix + '-TOTAL_FORMS'] = str(len(domain_set))
        for index, domain in enumerate(domain_set):
            post[prefix + '-' + str(index) + '-name'] = domain
        context['domain_formset'] = DomainFormSet(post)

        formset = context['domain_formset']
        if formset.is_valid():
            response = super().form_valid(form)
            formset.instance = self.object
            formset.save()
            return response
        else:
            for index, error in enumerate(formset.errors):
                if error.get('name'):
                    name = str(formset.forms[index].instance)
                    form.add_error('domains', '(' + name + ') ' + str(error.get('name').as_text()))
            return super().form_invalid(form)

