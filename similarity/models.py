from django.db import models
from django.conf import settings
from utils import generate_identifier

class SimilarityReport(models.Model):
    submission = models.ForeignKey('academics.Submission', on_delete=models.CASCADE, related_name='similarity_reports')
    report_id = models.CharField(max_length=40, unique=True, editable=False)
    similarity_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    matched_source_count = models.PositiveIntegerField()
    matched_segments = models.JSONField(default=list, blank=True)  # list of dicts with text and metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    rule_version = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.report_id:
            self.report_id = generate_identifier('SIM')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.report_id
