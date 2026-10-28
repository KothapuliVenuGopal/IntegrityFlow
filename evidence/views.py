from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import EvidenceItem

@login_required
def evidence_list(request):
    evidence_items = EvidenceItem.objects.all()
    return render(request, 'evidence/evidence_list.html', {'evidence_items': evidence_items})

@login_required
def evidence_detail(request, evidence_id):
    item = get_object_or_404(EvidenceItem, evidence_id=evidence_id)
    return render(request, 'evidence/evidence_detail.html', {'item': item})
