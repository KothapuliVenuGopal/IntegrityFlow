from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from academics.models import Learner, Assessment, Submission
from cases.models import Case, ReviewerAssignment, Decision, Appeal, ConflictOfInterest
from audit.models import CaseEvent
from cases.services import create_case, assign_reviewer, record_decision, submit_appeal

class CaseWorkflowTests(TestCase):
    def setUp(self):
        # Create users
        self.learner_user = User.objects.create_user(
            email='learner@example.com',
            password='Password123',
            role=User.Role.LEARNER
        )
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='Password123',
            role=User.Role.ADMIN
        )
        self.reviewer1 = User.objects.create_user(
            email='reviewer1@example.com',
            password='Password123',
            role=User.Role.REVIEWER
        )
        self.reviewer2 = User.objects.create_user(
            email='reviewer2@example.com',
            password='Password123',
            role=User.Role.REVIEWER
        )

        # Create learner and assessment
        self.learner = Learner.objects.create(user=self.learner_user)
        self.assessment = Assessment.objects.create(
            title='Computer Science 101 Final Exam',
            start_date=timezone.now() - timedelta(days=2),
            due_date=timezone.now() + timedelta(days=5),
        )
        self.submission = Submission.objects.create(
            learner=self.learner,
            assessment=self.assessment,
            content='My submission content with citations.',
            status='flagged'
        )

    def test_case_creation_and_audit(self):
        case = create_case(self.submission, self.admin_user, priority=2)
        self.assertTrue(case.case_id.startswith('INT-'))
        self.assertEqual(case.status, Case.Status.OPEN)
        
        # Verify audit event
        events = CaseEvent.objects.filter(case=case)
        self.assertEqual(events.count(), 1)
        self.assertEqual(events.first().event_type, CaseEvent.EventType.CREATED)

    def test_reviewer_assignment_and_conflict_prevention(self):
        case = create_case(self.submission, self.admin_user)
        
        # Declare conflict of interest for reviewer1
        ConflictOfInterest.objects.create(
            case=case,
            reviewer=self.reviewer1,
            reason='Mentored this student previously.'
        )

        # Attempt to assign reviewer with conflict should fail
        with self.assertRaises(ValueError) as ctx:
            assign_reviewer(case, self.reviewer1, self.admin_user)
        self.assertIn('conflict of interest', str(ctx.exception))

        # Assigning non-conflicted reviewer should succeed
        assignment = assign_reviewer(case, self.reviewer2, self.admin_user, notes='Assigned as primary')
        self.assertEqual(assignment.reviewer, self.reviewer2)

        # Verify audit event for assignment
        events = CaseEvent.objects.filter(case=case, event_type=CaseEvent.EventType.ASSIGNED)
        self.assertEqual(events.count(), 1)

    def test_record_decision(self):
        case = create_case(self.submission, self.admin_user)
        assign_reviewer(case, self.reviewer2, self.admin_user)

        decision = record_decision(
            case=case,
            reviewer=self.reviewer2,
            decision_type=Decision.DecisionType.NO_VIOLATION,
            rationale='Similarity corresponds to standard boilerplate header and properly cited quotes.'
        )
        case.refresh_from_db()
        self.assertEqual(case.status, Case.Status.DECIDED)
        self.assertTrue(decision.decision_id.startswith('DEC-'))

        # Verify audit event
        events = CaseEvent.objects.filter(case=case, event_type=CaseEvent.EventType.DECISION)
        self.assertEqual(events.count(), 1)

    def test_appeal_submission(self):
        case = create_case(self.submission, self.admin_user)
        record_decision(case, self.reviewer2, Decision.DecisionType.POLICY_VIOLATION, 'Uncited code snippet.')

        appeal = submit_appeal(
            case=case,
            learner_user=self.learner_user,
            grounds='Material procedural irregularity and misattributed sources.',
            statement='The snippet was provided in the course assignment handout directly.'
        )
        case.refresh_from_db()
        self.assertEqual(case.status, Case.Status.APPEAL_PENDING)
        self.assertTrue(appeal.appeal_id.startswith('APL-'))

        # Verify audit event
        events = CaseEvent.objects.filter(case=case, event_type=CaseEvent.EventType.APPEAL_SUBMITTED)
        self.assertEqual(events.count(), 1)
