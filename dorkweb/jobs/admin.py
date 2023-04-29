from django.contrib import admin
from .models import Job, Container


class JobAdmin(admin.ModelAdmin):
    list_display = ('id','organization','task')
    search_fields = ('organization',)
    readonly_fields = ('organization', 'domain', 'task',)


class ContainerAdmin(admin.ModelAdmin):
    list_display = ('id','job','organization','domain','host')
    search_fields = ('organization',)
    readonly_fields = ('job', 'organization', 'domain', 'host',)


admin.site.register(Job, JobAdmin)
admin.site.register(Container, ContainerAdmin)

