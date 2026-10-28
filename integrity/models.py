from django.db import models
from django.utils import timezone
from utils import generate_identifier

class IntegrityRule(models.Model):
    """Configurable integrity rule used to evaluate similarity reports.
    A rule can have multiple versions – each version is a separate record.
    """
    rule_id = models.CharField(max_length=30, unique=True, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    # Threshold is a percentage (e.g., 30.00) that, when exceeded, triggers a review.
    similarity_threshold = models.DecimalField(max_digits=5, decimal_places=2)
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], default='medium')
    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    effective_start = models.DateTimeField(default=timezone.now)
    effective_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-effective_start']
        unique_together = ('name', 'version')

    def save(self, *args, **kwargs):
        if not self.rule_id:
            self.rule_id = generate_identifier('RULE')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} v{self.version}"
