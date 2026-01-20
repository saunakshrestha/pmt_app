from django.db import models
from django.utils import timezone
from django.db.models import JSONField


class Estimate(models.Model):
    """Model for Estimate documents"""
    number = models.CharField(max_length=30, unique=True, blank=True, null=True)
    date = models.DateField(default=timezone.now, blank=True, null=True)
    valid_until = models.DateField(blank=True, null=True)
    
    customer_name = models.CharField(max_length=150, blank=True)
    customer_abn = models.CharField(max_length=20, blank=True)
    
    # Summary of customer requirements (HTML content)
    summary = models.TextField(blank=True, help_text="HTML formatted summary of customer requirements")
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)
    gst_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)
    
    # Terms & Conditions and Payment Terms (HTML content)
    terms_conditions = models.TextField(blank=True, help_text="HTML formatted terms and conditions")
    payment_terms = models.TextField(blank=True, help_text="HTML formatted payment terms")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Estimate {self.number or '(draft)'}"

    def calculate_totals(self, save=True):
        items = self.estimate_items.all()
        self.subtotal = sum(item.line_total_ex_gst for item in items)
        self.gst_total = sum(item.gst_amount for item in items)
        self.grand_total = self.subtotal + self.gst_total
        if save:
            self.save(update_fields=["subtotal", "gst_total", "grand_total"])


class Invoice(models.Model):
    """Model for Tax Invoice documents"""
    number = models.CharField(max_length=30, unique=True, blank=True, null=True)
    date = models.DateField(default=timezone.now, blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    
    customer_name = models.CharField(max_length=150, blank=True)
    customer_abn = models.CharField(max_length=20, blank=True)
    customer_address = models.TextField(blank=True)
    attention = models.CharField(max_length=100, blank=True)
    po_reference = models.CharField(max_length=50, blank=True)
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)
    gst_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invoice {self.number or '(draft)'}"

    def calculate_totals(self, save=True):
        items = self.invoice_items.all()
        self.subtotal = sum(item.line_total_ex_gst for item in items)
        self.gst_total = sum(item.gst_amount for item in items)
        self.grand_total = self.subtotal + self.gst_total
        if save:
            self.save(update_fields=["subtotal", "gst_total", "grand_total"])


class EstimateItem(models.Model):
    """Line items for Estimates"""
    estimate = models.ForeignKey(Estimate, related_name="estimate_items", on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, blank=True)

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


class InvoiceItem(models.Model):
    """Line items for Invoices"""
    invoice = models.ForeignKey(Invoice, related_name="invoice_items", on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, blank=True)

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


