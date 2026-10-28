from django.db import models
from django.conf import settings
from utils import generate_identifier

class CaseEvent(models.Model):
    """Immutable audit log entry for case timeline events."""
    class EventType(models.TextChoices):
        CREATED = 'created', 'Case Created'
        ASSIGNED = 'assigned', 'Reviewer Assigned'
        REASSIGNED = 'reassigned', 'Reviewer Reassigned'
        DECISION = 'decision', 'Decision Recorded'
        APPEAL_SUBMITTED = 'appeal_submitted', 'Appeal Submitted'
        APPEAL_DECISION = 'appeal_decision', 'Appeal Decision'
        EVIDENCE_ADDED = 'evidence_added', 'Evidence Added'
        EVIDENCE_UPDATED = 'evidence_updated', 'Evidence Updated'
        CONFLICT_DECLARED = 'conflict_declared', 'Conflict Declared'
        STATUS_CHANGE = 'status_change', 'Status Changed'

    event_id = models.CharField(max_length=30, unique=True, editable=False)
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if not self.event_id:
            self.event_id = generate_identifier('EVT')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.event_id} - {self.get_event_type_display()}"
