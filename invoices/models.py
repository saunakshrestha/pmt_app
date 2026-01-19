from django.db import models
from django.utils import timezone
from django.db.models import JSONField

class Document(models.Model):
    DOC_TYPE_CHOICES = [("estimate", "Estimate"), ("invoice", "Invoice")]

    doc_type = models.CharField(max_length=10, choices=DOC_TYPE_CHOICES)
    number = models.CharField(max_length=30, unique=True, blank=True)  # Auto-generated if blank
    date = models.DateField(default=timezone.now)
    valid_until = models.DateField(null=True, blank=True)  # Estimate only
    due_date = models.DateField(null=True, blank=True)     # Invoice only

    customer_name = models.CharField(max_length=150)
    customer_abn = models.CharField(max_length=20, blank=True)
    customer_address = models.TextField(blank=True)
    attention = models.CharField(max_length=100, blank=True)
    po_reference = models.CharField(max_length=50, blank=True)

    summary = JSONField(default=list, blank=True)  # List for numbered requirements, e.g., ["Item 1", "Item 2"]

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    terms_conditions = JSONField(default=dict, blank=True)  # e.g., {"text": "Your terms here"}
    payment_terms = JSONField(default=dict, blank=True)     # e.g., {"text": "Net 30 days"}
    extra_data = JSONField(default=dict, blank=True)        # For any custom fields, notes, etc.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.doc_type.title()} {self.number or '(draft)'}"

    def calculate_totals(self, save=True):
        items = self.items.all()
        self.subtotal = sum(item.line_total_ex_gst for item in items)
        self.gst_total = sum(item.gst_amount for item in items)
        self.grand_total = self.subtotal + self.gst_total
        if save:
            self.save(update_fields=["subtotal", "gst_total", "grand_total"])

class Item(models.Model):
    document = models.ForeignKey(Document, related_name="items", on_delete=models.CASCADE)
    description = models.TextField()
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)

    @property
    def line_total_ex_gst(self):
        return self.quantity * self.unit_price

    @property
    def gst_amount(self):
        return self.line_total_ex_gst * (self.gst_rate / 100)

    @property
    def line_total_inc_gst(self):
        return self.line_total_ex_gst + self.gst_amount

    def __str__(self):
        return self.description[:50]