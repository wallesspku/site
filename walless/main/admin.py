from django.contrib import admin
from . import models


class NodeAdmin(admin.ModelAdmin):
    ordering = ['node_id']  # Sort by 'node_id' in ascending order
    list_filter = ['deleted', 'hidden', 'tag']  # Add filters to the right side


admin.site.register(models.Push)
admin.site.register(models.User)
admin.site.register(models.Node, NodeAdmin)
admin.site.register(models.Relay)
admin.site.register(models.Probe)
admin.site.register(models.Registration)
admin.site.register(models.Sublog)
admin.site.register(models.Traffic)
admin.site.register(models.TrafficLog)
admin.site.register(models.Mix)
