from django.db import transaction
from .models import Case, ReviewerAssignment, Decision, Appeal, ConflictOfInterest
from audit.models import CaseEvent

def create_case(submission, created_by, priority=3, due_date=None):
    """Create a new case for a flagged submission and log the event."""
    with transaction.atomic():
        case = Case.objects.create(
            submission=submission,
            created_by=created_by,
            priority=priority,
            due_date=due_date,
        )
        CaseEvent.objects.create(
            case=case,
            event_type=CaseEvent.EventType.CREATED,
            performed_by=created_by,
            details={'submission_id': submission.submission_id},
        )
        return case

def assign_reviewer(case, reviewer, assigned_by, notes=''):
    """Assign a reviewer to a case, ensuring no conflict, and log."""
    if ConflictOfInterest.objects.filter(case=case, reviewer=reviewer).exists():
        raise ValueError('Reviewer has a declared conflict of interest for this case')
    with transaction.atomic():
        assignment, created = ReviewerAssignment.objects.get_or_create(
            case=case,
            reviewer=reviewer,
            defaults={'notes': notes},
        )
        if not created:
            raise ValueError('Reviewer already assigned to this case')
        CaseEvent.objects.create(
            case=case,
            event_type=CaseEvent.EventType.ASSIGNED,
            performed_by=assigned_by,
            details={'reviewer': reviewer.email},
        )
        return assignment

def record_decision(case, reviewer, decision_type, rationale):
    """Record a decision for a case and transition status."""
    with transaction.atomic():
        decision = Decision.objects.create(
            case=case,
            reviewer=reviewer,
            decision_type=decision_type,
            rationale=rationale,
        )
        case.status = Case.Status.DECIDED
        case.save()
        CaseEvent.objects.create(
            case=case,
            event_type=CaseEvent.EventType.DECISION,
            performed_by=reviewer,
            details={'decision_id': decision.decision_id, 'type': decision_type},
        )
        return decision

def submit_appeal(case, learner_user, grounds, statement):
    """Learner submits an appeal for a case."""
    with transaction.atomic():
        appeal = Appeal.objects.create(
            case=case,
            learner=learner_user,
            grounds=grounds,
            statement=statement,
        )
        case.status = Case.Status.APPEAL_PENDING
        case.save()
        CaseEvent.objects.create(
            case=case,
            event_type=CaseEvent.EventType.APPEAL_SUBMITTED,
            performed_by=learner_user,
            details={'appeal_id': appeal.appeal_id},
        )
        return appeal
