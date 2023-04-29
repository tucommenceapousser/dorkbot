from django.views import generic
from django.shortcuts import render
from .models import Job
from .forms import JobForm
from organizations.models import Domain
from django.conf import settings
import docker


class JobListView(generic.ListView):
    model = Job

    def get_context_data(self, **kwargs):
        docker_hosts = {}
        for key in settings.DOCKER_HOSTS:
            docker_host = settings.DOCKER_HOSTS[key]
            num_containers = self.get_num_containers(docker_host['url'])
            max_containers = docker_host['max_containers']
            docker_hosts[key] = [num_containers, max_containers]
        context = super(JobListView, self).get_context_data(**kwargs)
        context['docker_hosts'] = docker_hosts
        return context

    def get_num_containers(self, url):
        client = docker.DockerClient(base_url=url)
        num_containers = client.info()['ContainersRunning']
        return num_containers


class JobDetailView(generic.DetailView):
    model = Job


class JobCreateView(generic.CreateView):
    model = Job
    form_class = JobForm
    success_url = '/jobs/'


def load_domains(request):
    domains = Domain.objects.filter(organization=request.GET.get('organization'))
    return render(request, 'jobs/domain_options.html', {'domains': domains})

