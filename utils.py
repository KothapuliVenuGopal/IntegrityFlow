import datetime
from django.db import transaction, models

class IdentifierCounter(models.Model):
    """Atomic counter for deterministic identifiers per entity type."""
    prefix = models.CharField(max_length=20, unique=True)
    next_number = models.PositiveBigIntegerField(default=1)

    class Meta:
        db_table = "identifier_counter"
        app_label = "integrity"

def has_role(user, role):
    """Check if user has the given role (case‑insensitive)."""
    return getattr(user, 'role', '').lower() == role.lower()


def generate_identifier(prefix: str, digits: int = 6) -> str:
    """Generate a deterministic identifier like 'SUB-2026-000001'.
    The year component is the current calendar year. The numeric part is zero‑padded.
    """
    year = datetime.date.today().year
    with transaction.atomic():
        counter, _ = IdentifierCounter.objects.select_for_update().get_or_create(prefix=prefix)
        number = counter.next_number
        counter.next_number += 1
        counter.save()
    return f"{prefix}-{year}-{number:0{digits}d}"
