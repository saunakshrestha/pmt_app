from django import forms
from .models import Document

class DocumentForm(forms.ModelForm):
    summary = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False, label="Summary of Customer Requirements (numbered lines, one per line)")
    terms_conditions = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False, label="Terms & Conditions")
    payment_terms = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False, label="Payment Terms")

    class Meta:
        model = Document
        fields = [
            "doc_type", "number", "date", "valid_until", "due_date",
            "customer_name", "customer_abn", "customer_address",
            "attention", "po_reference", "summary",
            "terms_conditions", "payment_terms"
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "valid_until": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "customer_address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        doc_type = self.data.get("doc_type") or self.initial.get("doc_type", "estimate")
        if doc_type == "estimate":
            self.fields["due_date"].widget = forms.HiddenInput()
            self.fields["attention"].widget = forms.HiddenInput()
            self.fields["po_reference"].widget = forms.HiddenInput()
            self.fields["customer_address"].required = False
            self.fields["summary"].required = True
            self.fields["terms_conditions"].required = True
            self.fields["payment_terms"].required = True
        else:
            self.fields["valid_until"].widget = forms.HiddenInput()
            self.fields["summary"].widget = forms.HiddenInput()
            self.fields["terms_conditions"].widget = forms.HiddenInput()
            self.fields["payment_terms"].widget = forms.HiddenInput()

    def clean_summary(self):
        summary = self.cleaned_data.get("summary")
        if summary:
            return summary.splitlines()  # Store as list in JSONField
        return []

    def clean_terms_conditions(self):
        return {"text": self.cleaned_data.get("terms_conditions", "")}

    def clean_payment_terms(self):
        return {"text": self.cleaned_data.get("payment_terms", "")}