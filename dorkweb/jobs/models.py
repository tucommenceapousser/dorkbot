from django.db import models
from organizations.models import Organization, Domain
import docker
from background_task import background
from django.db.models.signals import post_save
from django.conf import settings
import os


class Job(models.Model):
    INDEX = 'index'
    SCAN = 'scan'
    TASK_TYPES = (
        (INDEX, 'Index'),
        (SCAN, 'Scan'),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, null=True, blank=True)
    task = models.CharField(max_length=5, choices=TASK_TYPES, default=INDEX)
    
    def __str__(self):
        return str(self.id) + '--' + self.organization.name + '--' + self.task


class Container(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, null=True, blank=True)
    host = models.CharField(max_length=128)

    def __str__(self):
        return 'dorkweb-' + str(self.job.id) + '-' + str(self.id)


@background()
def run_container(container_id):
    container = Container.objects.get(id=container_id)

    if 'postgres' in settings.DATABASES:
        db = settings.DATABASES['postgres']
        dorkbot_database = 'postgresql://' + ':'.join([db['USER'], db['PASSWORD']]) + '@' + ':'.join([db['HOST'], db['PORT']]) + '/' + settings.DORKBOT_DATABASE_PREFIX + container.organization.name
    else:
        dorkbot_database = os.path.join(os.sep, 'opt', 'dorkbot', settings.DORKBOT_DATABASE_PREFIX + container.organization.name + '.sqlite3')

    if 'blacklist' in settings.DATABASES:
        db = settings.DATABASES['blacklist']
        blacklist = 'postgresql://' + ':'.join([db['USER'], db['PASSWORD']]) + '@' + ':'.join([db['HOST'], db['PORT']]) + '/' + settings.DORKBOT_DATABASE_PREFIX + 'blacklist'
    else:
        blacklist = os.path.join(os.sep, 'opt', 'dorkbot', 'config', 'blacklist.txt')

    cmd = ['/bin/bash']
    cmd += ['-c', 'pip3', 'install', '--upgrade', 'dorkbot', '&&']
    cmd += ['dorkbot']
    cmd += ['-r', '/opt/dorkbot']
    cmd += ['-d', dorkbot_database]
    cmd += ['-b', blacklist]
    if settings.DEBUG:
        cmd += ['-v']
    if container.job.task == 'index':
        cmd += ['--log', 'reports/index-commoncrawl_' + container.organization.name + '_' + container.domain.name + '.log']
        cmd += ['-i', 'commoncrawl']
        cmd += ['-o', 'domain=' + container.domain.name]
        cmd += ['-u']
        cmd += ['-p', 'random']
    elif container.job.task == 'scan':
        num_pages_to_scan = 1
        default_checks = ["active/*", "-csrf", "-unvalidated_redirect", "-source_code_disclosure", "-response_splitting", "-no_sql_injection_differential"]
        scan_timeout = 60 * 60
        user_agent = 'UT-Dorkbot/1.2'
        cmd += ['--log', 'reports/scan-' + container.organization.name + '.log']
        cmd += ['-s', 'arachni']
        cmd += ['-p', 'random']
        cmd += ['-p', 'count=' + str(num_pages_to_scan)]
        cmd += ['-p', 'label=' + container.organization.name]
        cmd += ['-p', 'args=' + '--checks ' + ','.join(default_checks) + \
                           ' --timeout ' + str(scan_timeout) + \
                           ' --http-request-redirect-limit 0' + \
                           ' --http-request-concurrency 1' + \
                           ' --browser-cluster-pool-size 1' + \
                           ' --plugin rate_limiter:requests_per_second=1' + \
                           ' --http-user-agent ' + user_agent + \
                           ' --daemon-friendly']

    docker_host = settings.DOCKER_HOSTS[settings.DOCKER_DEFAULT_HOST]
    client = docker.DockerClient(base_url=docker_host['url'])
    c = client.containers.run(image=docker_host['image'], command=cmd, name=str(container), detach=True, stdin_open=True, tty=True, auto_remove=True, read_only=True, network_mode='host', user=':'.join([docker_host['uid'], docker_host['gid']]), volumes={os.path.join(os.path.normpath(settings.DORKBOT_DIRECTORY), '.local'): {'bind': '/opt/dorkbot/.local', 'mode': 'ro'}, os.path.join(os.path.normpath(settings.DORKBOT_DIRECTORY), 'tools'): {'bind': '/opt/dorkbot/tools', 'mode': 'rw'}, os.path.join(os.path.normpath(settings.DORKBOT_DIRECTORY), 'reports'): {'bind': '/opt/dorkbot/reports', 'mode': 'rw'},}, working_dir='/opt/dorkbot', environment={'HOME': '/opt/dorkbot', 'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/dorkbot/.local/bin'}, log_config={'type': 'none'}, tmpfs={'/tmp': 'size=512M'})

    c.wait()
    container.delete()

    if not Container.objects.filter(job=container.job):
        container.job.delete()


def schedule_containers(sender, instance, **kwargs):
    docker_host = settings.DOCKER_HOSTS[settings.DOCKER_DEFAULT_HOST]
    if instance.organization.enabled:
        if instance.task == 'index':
            if instance.domain:
                container = Container(job=instance, organization=instance.organization, domain=instance.domain, host=docker_host['url'])
                container.save()
            else:
                for domain in Domain.objects.filter(organization=instance.organization.id):
                    container = Container(job=instance, organization=instance.organization, domain=domain, host=docker_host['url'])
                    container.save()
        elif instance.task == 'scan':
            container = Container(job=instance, organization=instance.organization, domain=instance.domain, host=docker_host['url'])
            container.save()

        for container in Container.objects.filter(job=instance):
            run_container(container.id)


post_save.connect(schedule_containers, sender=Job)

