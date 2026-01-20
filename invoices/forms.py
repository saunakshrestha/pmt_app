from django import forms
from tinymce.widgets import TinyMCE
from .models import Estimate, Invoice


class EstimateForm(forms.ModelForm):
    """Form for creating/editing Estimates"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional
        for field in self.fields.values():
            field.required = False
    
    class Meta:
        model = Estimate
        fields = [
            "customer_name", "customer_abn", "number", "date", "valid_until",
            "summary", "terms_conditions", "payment_terms"
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "valid_until": forms.DateInput(attrs={"type": "date"}),
            "customer_name": forms.TextInput(attrs={"placeholder": "e.g., IPS Design"}),
            "customer_abn": forms.TextInput(attrs={"placeholder": "e.g., 12 345 678 901"}),
            "number": forms.TextInput(attrs={"placeholder": "Auto-generated if left blank"}),
            "summary": TinyMCE(attrs={
                "placeholder": "Enter summary of customer requirements. You can use basic HTML formatting."
            }),
            "terms_conditions": TinyMCE(attrs={
                "placeholder": "Enter terms and conditions. You can use basic HTML formatting."
            }),
            "payment_terms": TinyMCE(attrs={
                "placeholder": "e.g., Net 30 days"
            }),
        }
        labels = {
            "customer_name": "Customer Name",
            "customer_abn": "Customer ABN",
            "number": "Estimate Number (optional)",
            "date": "Date",
            "valid_until": "Estimate Valid Until",
            "summary": "Summary of Customer Requirements",
            "terms_conditions": "Terms & Conditions",
            "payment_terms": "Payment Terms",
        }
        help_texts = {
            "summary": "Enter requirements in numbered format. Each line will be automatically numbered when displayed.",
            "terms_conditions": "Enter your terms and conditions. You can use HTML for formatting.",
            "payment_terms": "Specify payment terms (e.g., Net 30 days, Due on receipt)",
        }


class InvoiceForm(forms.ModelForm):
    """Form for creating/editing Tax Invoices"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional
        for field in self.fields.values():
            field.required = False
    
    class Meta:
        model = Invoice
        fields = [
            "customer_name", "attention", "customer_address", "customer_abn",
            "number", "date", "due_date", "po_reference"
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "customer_name": forms.TextInput(attrs={"placeholder": "e.g., IPS Global Pty Ltd"}),
            "attention": forms.TextInput(attrs={"placeholder": "e.g., Ryan Shackleton"}),
            "customer_address": forms.Textarea(attrs={"rows": 3, "placeholder": "PO BOX 2046 MARMION WA 6020\nAUSTRALIA"}),
            "customer_abn": forms.TextInput(attrs={"placeholder": "e.g., 67 667 059 458"}),
            "number": forms.TextInput(attrs={"placeholder": "Auto-generated if left blank"}),
            "po_reference": forms.TextInput(attrs={"placeholder": "e.g., PO-0015"}),
        }
        labels = {
            "customer_name": "Customer Name",
            "attention": "Attention",
            "customer_address": "Customer Address",
            "customer_abn": "ABN",
            "number": "Invoice Number (optional)",
            "date": "Invoice Date",
            "due_date": "Due Date",
            "po_reference": "Reference/PO #",
        }


# Keep old form for backward compatibility (optional)
class DocumentForm(forms.ModelForm):
    summary = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False, label="Summary of Customer Requirements (numbered lines, one per line)")
    terms_conditions = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False, label="Terms & Conditions")
    payment_terms = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False, label="Payment Terms")

    class Meta:
        model = Invoice  # Changed from Document
        fields = [
            "number", "date", "due_date",
            "customer_name", "customer_abn", "customer_address",
            "attention", "po_reference"
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "customer_address": forms.Textarea(attrs={"rows": 3}),
        }