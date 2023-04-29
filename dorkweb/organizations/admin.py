from django.contrib import admin
from .models import Organization, Domain
from django.contrib.admin import site

site.disable_action('delete_selected')

class DomainInline(admin.TabularInline):
    model = Domain


class OrganizationAdmin(admin.ModelAdmin):
    inlines = [DomainInline]
    list_display = ('name', 'enabled',)
    list_filter = ('enabled',)
    search_fields = ('name',)
    readonly_fields = ('total_targets', 'scanned_targets', 'unscanned_targets', 'fingerprint_count',)


class DomainAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization',)
    search_fields = ('name', 'organization__name',)
    readonly_fields = ('organization',)


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Domain, DomainAdmin)

