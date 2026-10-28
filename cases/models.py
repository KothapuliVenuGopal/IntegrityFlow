from django.db import models
from django.conf import settings
from utils import generate_identifier

class Case(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_REVIEW = 'in_review', 'In Review'
        DECIDED = 'decided', 'Decided'
        APPEAL_PENDING = 'appeal_pending', 'Appeal Pending'
        CLOSED = 'closed', 'Closed'
        REOPENED = 'reopened', 'Reopened'

    case_id = models.CharField(max_length=30, unique=True, editable=False)
    submission = models.ForeignKey('academics.Submission', on_delete=models.PROTECT, related_name='cases')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='cases_created')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.PositiveSmallIntegerField(default=3)  # 1=high,5=low
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.case_id:
            self.case_id = generate_identifier('INT')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.case_id

class ReviewerAssignment(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='assignments')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={'role': 'reviewer'}, on_delete=models.PROTECT, related_name='assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    conflict_declared = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('case', 'reviewer')

    def __str__(self):
        return f"{self.case.case_id} - {self.reviewer.email}"

class Decision(models.Model):
    class DecisionType(models.TextChoices):
        NO_VIOLATION = 'no_violation', 'No Violation'
        INCONCLUSIVE = 'inconclusive', 'Inconclusive'
        POLICY_VIOLATION = 'policy_violation', 'Policy Violation'
        ADDITIONAL_EVIDENCE_REQUIRED = 'additional_evidence', 'Additional Evidence Required'

    decision_id = models.CharField(max_length=30, unique=True, editable=False)
    case = models.ForeignKey(Case, on_delete=models.PROTECT, related_name='decisions')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={'role': 'reviewer'}, on_delete=models.PROTECT, related_name='decisions')
    decision_type = models.CharField(max_length=30, choices=DecisionType.choices)
    rationale = models.TextField()
    decided_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.decision_id:
            self.decision_id = generate_identifier('DEC')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.decision_id} ({self.get_decision_type_display()})"

class Appeal(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        UNDER_REVIEW = 'under_review', 'Under Review'
        RESOLVED = 'resolved', 'Resolved'
        REJECTED = 'rejected', 'Rejected'

    appeal_id = models.CharField(max_length=30, unique=True, editable=False)
    case = models.ForeignKey(Case, on_delete=models.PROTECT, related_name='appeals')
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={'role': 'learner'}, on_delete=models.PROTECT, related_name='appeals')
    grounds = models.TextField()
    statement = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={'role': 'reviewer'}, null=True, blank=True, on_delete=models.PROTECT, related_name='appeal_reviews')
    outcome = models.CharField(max_length=30, blank=True)  # UPHELD, OVERTURNED, etc.
    rationale = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.appeal_id:
            self.appeal_id = generate_identifier('APL')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.appeal_id

class ConflictOfInterest(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='conflicts')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={'role': 'reviewer'}, on_delete=models.CASCADE)
    declared_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField()

    class Meta:
        unique_together = ('case', 'reviewer')

    def __str__(self):
        return f"Conflict: {self.reviewer.email} on {self.case.case_id}"
