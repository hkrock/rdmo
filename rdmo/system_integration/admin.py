from django.contrib import admin

# Register your models here.
from .models import Catalog2ExternalDatamodel


class cat2extAdmin(admin.ModelAdmin):
    list_display = ('catalog', 'datamodel')

admin.site.register(Catalog2ExternalDatamodel, cat2extAdmin)
