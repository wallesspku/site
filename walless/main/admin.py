from django.contrib import admin
from . import models
from walless_utils import data_format


class NodeAdmin(admin.ModelAdmin):
    ordering = ['node_id']  # Sort by 'node_id' in ascending order
    list_filter = ['deleted', 'hidden', 'tag']  # Add filters to the right side
    list_display = ['name', 'visible', 'node_id', 'idc', 'tag', 'traffic']

    @admin.decorators.display(description='visible', boolean=True)
    def visible(self, obj):
        return not obj.hidden and not obj.deleted
    
    @admin.decorators.display(description='traffic', boolean=False, ordering='download')
    def traffic(self, obj) -> float:
        return data_format(obj.upload + obj.download, decimal=True)
    
    fieldsets = [
        (
            None,
            {
                "fields": ["node_id", "name", "weight", "ipv4", "ipv6", 'idc', 'remarks'],
            },
        ),
        (
            "Advanced",
            {
                "fields": ["hidden", "deleted", 'tag', 'properties'],
            },
        ),
    ]


class UserAdmin(admin.ModelAdmin):
    ordering = ['user_id']
    list_filter = ['tag', 'enabled']
    list_display = ['email', 'user_id', 'tag', 'enabled', 'traffic']
    search_fields = ['email', 'user_id']
    
    @admin.decorators.display(description='traffic', boolean=False, ordering='download')
    def traffic(self, obj) -> float:
        return data_format(obj.upload + obj.download, decimal=True)
    
    fields = ['enabled', 'email', 'password', 'tag', 'last_change', 'balance', 'remarks']


class RelayAdmin(admin.ModelAdmin):
    ordering = ['relay_id']
    list_display = ['relay_id', 'source', 'target']


class MixAdmin(admin.ModelAdmin):
    list_display = ['id', 'source', 'target']


admin.site.register(models.Push)
admin.site.register(models.User, UserAdmin)
admin.site.register(models.Node, NodeAdmin)
admin.site.register(models.Relay, RelayAdmin)
admin.site.register(models.Mix, MixAdmin)
# admin.site.register(models.Probe)
# admin.site.register(models.Registration)
# admin.site.register(models.Sublog)
# admin.site.register(models.Traffic)
# admin.site.register(models.TrafficLog)
