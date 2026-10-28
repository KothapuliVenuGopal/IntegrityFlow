from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Assessment, Submission, Learner
from utils import has_role

@login_required
def assessment_list(request):
    """List all assessments visible to the user."""
    # Instructors and admins see all; learners see only those they are enrolled in (simplified as all)
    if has_role(request.user, 'learner'):
        assessments = Assessment.objects.all()
    else:
        assessments = Assessment.objects.all()
    return render(request, 'academics/assessment_list.html', {'assessments': assessments})

@login_required
def assessment_detail(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk)
    return render(request, 'academics/assessment_detail.html', {'assessment': assessment})

@login_required
def submission_list(request):
    """List submissions for the current user (learners) or all for staff."""
    if has_role(request.user, 'learner'):
        submissions = Submission.objects.filter(learner__user=request.user)
    else:
        submissions = Submission.objects.all()
    return render(request, 'academics/submission_list.html', {'submissions': submissions})

@login_required
def submission_create(request):
    """Create a new submission for a learner. Only learners may submit."""
    if not has_role(request.user, 'learner'):
        raise PermissionDenied('Only learners can submit assessments')
    if request.method == 'POST':
        assessment_id = request.POST.get('assessment')
        content = request.POST.get('content', '')
        assessment = get_object_or_404(Assessment, pk=assessment_id)
        learner = get_object_or_404(Learner, user=request.user)
        Submission.objects.create(
            learner=learner,
            assessment=assessment,
            content=content,
        )
        return redirect('submission_list')
    else:
        assessments = Assessment.objects.all()
        return render(request, 'academics/submission_form.html', {'assessments': assessments})
