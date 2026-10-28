from django.db import models
from django.conf import settings
from utils import generate_identifier

class EvidenceItem(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = 'public', 'Public'
        RESTRICTED = 'restricted', 'Restricted'
        INTERNAL = 'internal', 'Internal'

    evidence_id = models.CharField(max_length=30, unique=True, editable=False)
    case = models.ForeignKey('cases.Case', on_delete=models.PROTECT, related_name='evidence_items')
    evidence_type = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    source_reference = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to='evidence/', blank=True, null=True)
    checksum = models.CharField(max_length=64, blank=True)  # SHA256 hex
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='evidence_added')
    created_at = models.DateTimeField(auto_now_add=True)
    provenance = models.JSONField(default=dict, blank=True)
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.INTERNAL)
    version = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        if not self.evidence_id:
            self.evidence_id = generate_identifier('EVD')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.evidence_id
