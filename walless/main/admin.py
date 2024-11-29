from django.contrib import admin
from . import models


admin.site.register(models.Push)

admin.site.register(models.User)
admin.site.register(models.Node)
admin.site.register(models.Relay)
admin.site.register(models.Probe)
admin.site.register(models.Registration)
admin.site.register(models.Sublog)
admin.site.register(models.Traffic)
admin.site.register(models.TrafficLog)
admin.site.register(models.Mix)
