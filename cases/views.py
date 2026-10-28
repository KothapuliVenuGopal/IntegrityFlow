from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from utils import has_role
from .models import Case, ReviewerAssignment, Decision, Appeal
from . import services

@login_required
def case_list(request):
    """List cases visible to the user based on role."""
    if has_role(request.user, 'learner'):
        # Learners see cases for their submissions only
        cases = Case.objects.filter(submission__learner__user=request.user)
    elif has_role(request.user, 'reviewer'):
        # Reviewers see cases assigned to them
        cases = Case.objects.filter(assignments__reviewer=request.user)
    else:
        # Admins, instructors, support see all
        cases = Case.objects.all()
    return render(request, 'cases/case_list.html', {'cases': cases})

@login_required
def case_detail(request, case_id):
    case = get_object_or_404(Case, case_id=case_id)
    # Permission check – only participants can view
    if has_role(request.user, 'learner'):
        if not case.submission.learner.user == request.user:
            raise PermissionDenied
    elif has_role(request.user, 'reviewer'):
        if not case.assignments.filter(reviewer=request.user).exists():
            raise PermissionDenied
    return render(request, 'cases/case_detail.html', {'case': case})

@login_required
def assign_reviewer(request, case_id):
    if not has_role(request.user, 'admin') and not has_role(request.user, 'instructor'):
        raise PermissionDenied('Only admins or instructors can assign reviewers')
    case = get_object_or_404(Case, case_id=case_id)
    if request.method == 'POST':
        reviewer_email = request.POST.get('reviewer')
        reviewer = get_object_or_404(request.user.__class__, email=reviewer_email, role='reviewer')
        services.assign_reviewer(case, reviewer, assigned_by=request.user)
        return redirect('case_detail', case_id=case.case_id)
    # Show simple form of available reviewers
    reviewers = request.user.__class__.objects.filter(role='reviewer')
    return render(request, 'cases/assign_reviewer.html', {'case': case, 'reviewers': reviewers})

@login_required
def record_decision(request, case_id):
    if not has_role(request.user, 'reviewer'):
        raise PermissionDenied('Only reviewers can record decisions')
    case = get_object_or_404(Case, case_id=case_id)
    if request.method == 'POST':
        decision_type = request.POST.get('decision_type')
        rationale = request.POST.get('rationale', '')
        services.record_decision(case, request.user, decision_type, rationale)
        return redirect('case_detail', case_id=case.case_id)
    return render(request, 'cases/record_decision.html', {'case': case, 'decision_choices': Decision.DecisionType.choices})

@login_required
def submit_appeal(request, case_id):
    if not has_role(request.user, 'learner'):
        raise PermissionDenied('Only learners can submit appeals')
    case = get_object_or_404(Case, case_id=case_id)
    if request.method == 'POST':
        grounds = request.POST.get('grounds', '')
        statement = request.POST.get('statement', '')
        services.submit_appeal(case, request.user, grounds, statement)
        return redirect('case_detail', case_id=case.case_id)
    return render(request, 'cases/submit_appeal.html', {'case': case})

