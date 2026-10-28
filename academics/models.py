from django.db import models
from django.conf import settings
from utils import generate_identifier

class Learner(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learner_profile')
    learner_id = models.CharField(max_length=20, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.learner_id:
            self.learner_id = generate_identifier('LRN')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.learner_id

class Assessment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    due_date = models.DateTimeField()
    assessment_id = models.CharField(max_length=20, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.assessment_id:
            self.assessment_id = generate_identifier('ASM')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.assessment_id}: {self.title}"

class Submission(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name='submissions')
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    content = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    submission_id = models.CharField(max_length=30, unique=True, editable=False)
    # status can be 'pending', 'flagged', 'under_review', 'closed'
    status = models.CharField(max_length=20, default='pending')

    def save(self, *args, **kwargs):
        if not self.submission_id:
            self.submission_id = generate_identifier('SUB')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.submission_id
