from django.db import models
from django.utils.translation import ugettext_lazy as _
from rdmo.questions.models import Catalog

# Create your models here.
class Catalog2ExternalDatamodel(models.Model):
    catalog = models.ForeignKey(
        Catalog, related_name='usesDatamodel', on_delete=models.CASCADE, null=False,
        verbose_name=_('Catalog'),
        help_text=_('The catalog which will be used for this project.')
    )
    datamodel = models.IntegerField(blank = False, null = False)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['catalog'], name='uniqueCatalog2Model')
        ]
