from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SimilarityReport
from utils import has_role

@login_required
def similarity_list(request):
    reports = SimilarityReport.objects.all()
    return render(request, 'similarity/similarity_list.html', {'reports': reports})

@login_required
def similarity_detail(request, report_id):
    report = get_object_or_404(SimilarityReport, report_id=report_id)
    return render(request, 'similarity/similarity_detail.html', {'report': report})
