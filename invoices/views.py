from decimal import Decimal
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.utils import timezone
from datetime import date, timedelta
from weasyprint import HTML
from .forms import EstimateForm, InvoiceForm, DocumentForm
from .models import Estimate, EstimateItem, Invoice, InvoiceItem, Document, Item


# PORTAL HOME
def invoices_home(request):
    """Invoice & Estimate Portal Homepage"""
    # Get statistics
    total_estimates = Estimate.objects.count()
    total_invoices = Invoice.objects.count()
    
    # Count documents created this month
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    recent_estimates = Estimate.objects.filter(created_at__gte=current_month_start).count()
    recent_invoices = Invoice.objects.filter(created_at__gte=current_month_start).count()
    recent_count = recent_estimates + recent_invoices
    
    context = {
        'total_estimates': total_estimates,
        'total_invoices': total_invoices,
        'recent_count': recent_count,
    }
    return render(request, 'invoices/portal_home.html', context)


# ESTIMATE VIEWS
@login_required
def create_estimate(request, estimate_id=None):
    """Create a new estimate or edit existing one"""
    estimate_instance = None
    existing_items = []
    
    if estimate_id:
        estimate_instance = Estimate.objects.get(id=estimate_id)
        existing_items = EstimateItem.objects.filter(estimate=estimate_instance)
    
    if request.method == "POST":
        form = EstimateForm(request.POST)
        if form.is_valid():
            # Collect items
            item_count = int(request.POST.get("item_count", 0))
            items = []
            subtotal = Decimal("0")
            gst_total = Decimal("0")
            
            for i in range(item_count):
                desc = request.POST.get(f"item_{i}_description")
                if not desc:
                    continue
                qty = int(request.POST.get(f"item_{i}_quantity", 1))
                unit_price = Decimal(request.POST.get(f"item_{i}_unit_price", "0"))
                gst_rate = Decimal(request.POST.get(f"item_{i}_gst_rate", "10"))
                
                line_sub = qty * unit_price
                line_gst = line_sub * (gst_rate / 100)
                items.append({
                    "description": desc,
                    "quantity": qty,
                    "unit_price": float(unit_price),
                    "gst_rate": float(gst_rate),
                    "line_total_inc_gst": float(line_sub + line_gst),
                })
                subtotal += line_sub
                gst_total += line_gst

            grand_total = subtotal + gst_total

            # Session data for preview
            estimate_data = {
                "customer_name": form.cleaned_data["customer_name"],
                "customer_abn": form.cleaned_data["customer_abn"],
                "number": form.cleaned_data["number"] or "DRAFT",
                "date": form.cleaned_data["date"].isoformat() if form.cleaned_data["date"] else None,
                "valid_until": form.cleaned_data["valid_until"].isoformat() if form.cleaned_data["valid_until"] else None,
                "summary": form.cleaned_data["summary"],  # HTML content
                "terms_conditions": form.cleaned_data["terms_conditions"],  # HTML content
                "payment_terms": form.cleaned_data["payment_terms"],  # HTML content
                "subtotal": float(subtotal),
                "gst_total": float(gst_total),
                "grand_total": float(grand_total),
                "items": items,
            }
            request.session["temp_estimate"] = estimate_data

            action = request.POST.get("action")
            
            if action == "preview":
                # Just show preview without saving to DB
                return redirect("preview_estimate")
            
            elif action == "save":
                # Save to database and show preview
                if estimate_instance:
                    # Update existing estimate
                    estimate = estimate_instance
                    # Update fields from form
                    for field in form.cleaned_data:
                        setattr(estimate, field, form.cleaned_data[field])
                    # Delete old items
                    EstimateItem.objects.filter(estimate=estimate_instance).delete()
                else:
                    # Create new estimate
                    estimate = form.save(commit=False)
                    if not estimate.number:
                        max_num = Estimate.objects.aggregate(max_num=Max("number"))["max_num"]
                        if max_num and max_num.isdigit():
                            estimate.number = str(int(max_num) + 1)
                        else:
                            estimate.number = "2025001"
                
                estimate.subtotal = subtotal
                estimate.gst_total = gst_total
                estimate.grand_total = grand_total
                estimate.save()

                # Save items
                for item_data in items:
                    EstimateItem.objects.create(
                        estimate=estimate,
                        description=item_data["description"],
                        quantity=item_data["quantity"],
                        unit_price=item_data["unit_price"],
                        gst_rate=item_data["gst_rate"]
                    )

                request.session["temp_estimate"]["number"] = estimate.number
                request.session["estimate_saved"] = True
                messages.success(request, f"✅ Estimate {estimate.number} saved successfully!")
                return redirect("preview_estimate")
            
            elif action == "download":
                # Save to database first, then download PDF
                if estimate_instance:
                    # Update existing estimate
                    estimate = estimate_instance
                    # Update fields from form
                    for field in form.cleaned_data:
                        setattr(estimate, field, form.cleaned_data[field])
                    # Delete old items
                    EstimateItem.objects.filter(estimate=estimate_instance).delete()
                else:
                    # Create new estimate
                    estimate = form.save(commit=False)
                    if not estimate.number:
                        max_num = Estimate.objects.aggregate(max_num=Max("number"))["max_num"]
                        if max_num and max_num.isdigit():
                            estimate.number = str(int(max_num) + 1)
                        else:
                            estimate.number = "2025001"
                
                estimate.subtotal = subtotal
                estimate.gst_total = gst_total
                estimate.grand_total = grand_total
                estimate.save()

                # Save items
                for item_data in items:
                    EstimateItem.objects.create(
                        estimate=estimate,
                        description=item_data["description"],
                        quantity=item_data["quantity"],
                        unit_price=item_data["unit_price"],
                        gst_rate=item_data["gst_rate"]
                    )

                request.session["temp_estimate"]["number"] = estimate.number
                request.session["estimate_saved"] = True
                return redirect("export_estimate_pdf")

            return redirect("preview_estimate")
        else:
            messages.error(request, "Form errors - please check fields.")

    else:
        if estimate_instance:
            # Pre-populate form with existing data
            form = EstimateForm(instance=estimate_instance)
        else:
            form = EstimateForm()

    return render(request, "invoices/estimate_form.html", {
        "form": form,
        "existing_items": existing_items,
        "is_edit": estimate_instance is not None,
    })


@login_required
def preview_estimate(request):
    """Preview an estimate before exporting"""
    data = request.session.get("temp_estimate")
    if not data:
        messages.warning(request, "No data - create estimate first.")
        return redirect("create_estimate")
    
    # Convert date strings to date objects for display
    if data.get("date") and isinstance(data.get("date"), str):
        data["date"] = date.fromisoformat(data["date"])
    if data.get("valid_until") and isinstance(data.get("valid_until"), str):
        data["valid_until"] = date.fromisoformat(data["valid_until"])
    
    return render(request, "invoices/estimate_preview.html", {"estimate": data})


@login_required
def save_estimate_from_preview(request):
    """Save estimate from preview page if not already saved"""
    if request.method != "POST":
        return redirect("preview_estimate")
    
    # Check if already saved
    if request.session.get("estimate_saved"):
        messages.info(request, "Estimate already saved!")
        return redirect("preview_estimate")
    
    data = request.session.get("temp_estimate")
    if not data:
        messages.warning(request, "No data - create estimate first.")
        return redirect("create_estimate")
    
    # Save to database
    estimate = Estimate(
        customer_name=data["customer_name"],
        customer_abn=data["customer_abn"],
        number=data["number"] if data["number"] != "DRAFT" else None,
        date=date.fromisoformat(data["date"]) if data.get("date") and isinstance(data["date"], str) else data.get("date"),
        valid_until=date.fromisoformat(data["valid_until"]) if data.get("valid_until") and isinstance(data["valid_until"], str) else data.get("valid_until"),
        summary=data["summary"],
        terms_conditions=data["terms_conditions"],
        payment_terms=data["payment_terms"],
        subtotal=Decimal(str(data["subtotal"])),
        gst_total=Decimal(str(data["gst_total"])),
        grand_total=Decimal(str(data["grand_total"]))
    )
    
    if not estimate.number:
        max_num = Estimate.objects.aggregate(max_num=Max("number"))["max_num"]
        if max_num and max_num.isdigit():
            estimate.number = str(int(max_num) + 1)
        else:
            estimate.number = "2025001"
    
    estimate.save()
    
    # Save items
    for item_data in data["items"]:
        EstimateItem.objects.create(
            estimate=estimate,
            description=item_data["description"],
            quantity=Decimal(str(item_data["quantity"])),
            unit_price=Decimal(str(item_data["unit_price"])),
            gst_rate=Decimal(str(item_data["gst_rate"]))
        )
    
    request.session["temp_estimate"]["number"] = estimate.number
    request.session["estimate_saved"] = True
    messages.success(request, f"✅ Estimate {estimate.number} saved successfully!")
    
    return redirect("preview_estimate")


@login_required
def export_estimate_pdf(request):
    """Export estimate as PDF"""
    data = request.session.get("temp_estimate")
    if not data:
        return HttpResponse("No data.", status=400)

    # Convert date strings to date objects for template
    if data.get("date") and isinstance(data.get("date"), str):
        data["date"] = date.fromisoformat(data["date"])
    if data.get("valid_until") and isinstance(data.get("valid_until"), str):
        data["valid_until"] = date.fromisoformat(data["valid_until"])

    html_string = render(request, "invoices/estimate_preview.html", {"estimate": data}).content.decode("utf-8")
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="Estimate_{data["number"]}.pdf"'
    return response


# INVOICE VIEWS
@login_required
def create_invoice(request, invoice_id=None):
    """Create a new tax invoice or edit existing one"""
    invoice_instance = None
    existing_items = []
    
    if invoice_id:
        invoice_instance = Invoice.objects.get(id=invoice_id)
        existing_items = InvoiceItem.objects.filter(invoice=invoice_instance)
    
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        if form.is_valid():
            # Collect items
            item_count = int(request.POST.get("item_count", 0))
            items = []
            subtotal = Decimal("0")
            gst_total = Decimal("0")
            
            for i in range(item_count):
                desc = request.POST.get(f"item_{i}_description")
                if not desc:
                    continue
                qty = int(request.POST.get(f"item_{i}_quantity", 1))
                unit_price = Decimal(request.POST.get(f"item_{i}_unit_price", "0"))
                gst_rate = Decimal(request.POST.get(f"item_{i}_gst_rate", "0.1"))
                
                line_sub = qty * unit_price
                line_gst = line_sub * gst_rate
                items.append({
                    "description": desc,
                    "quantity": qty,
                    "unit_price": float(unit_price),
                    "gst_rate": float(gst_rate),
                    "line_total_inc_gst": float(line_sub + line_gst),
                })
                subtotal += line_sub
                gst_total += line_gst

            grand_total = subtotal + gst_total

            # Session data for preview
            invoice_data = {
                "customer_name": form.cleaned_data["customer_name"],
                "attention": form.cleaned_data["attention"],
                "customer_address": form.cleaned_data["customer_address"],
                "customer_abn": form.cleaned_data["customer_abn"],
                "number": form.cleaned_data["number"] or "DRAFT",
                "date": form.cleaned_data["date"].isoformat() if form.cleaned_data["date"] else None,
                "due_date": form.cleaned_data["due_date"].isoformat() if form.cleaned_data["due_date"] else None,
                "po_reference": form.cleaned_data["po_reference"],
                "subtotal": float(subtotal),
                "gst_total": float(gst_total),
                "grand_total": float(grand_total),
                "items": items,
            }
            request.session["temp_invoice"] = invoice_data

            action = request.POST.get("action")
            
            if action == "preview":
                # Just show preview without saving to DB
                return redirect("preview_invoice")
            
            elif action == "save":
                # Save to database and show preview
                if invoice_instance:
                    # Update existing invoice
                    invoice = invoice_instance
                    # Update fields from form
                    for field in form.cleaned_data:
                        setattr(invoice, field, form.cleaned_data[field])
                    # Delete old items
                    InvoiceItem.objects.filter(invoice=invoice_instance).delete()
                else:
                    # Create new invoice
                    invoice = form.save(commit=False)
                    if not invoice.number:
                        year = invoice.date.year if invoice.date else timezone.now().year
                        max_seq = Invoice.objects.filter(number__startswith=f"MO-{year}-").aggregate(
                            max_seq=Max("number"))["max_seq"]
                        if max_seq:
                            seq = int(max_seq.split("-")[-1]) + 1
                        else:
                            seq = 1
                        invoice.number = f"MO-{year}-{seq:02d}"
                
                invoice.subtotal = subtotal
                invoice.gst_total = gst_total
                invoice.grand_total = grand_total
                invoice.save()

                # Save items
                for item_data in items:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        description=item_data["description"],
                        quantity=item_data["quantity"],
                        unit_price=item_data["unit_price"],
                        gst_rate=item_data["gst_rate"]
                    )

                request.session["temp_invoice"]["number"] = invoice.number
                request.session["invoice_saved"] = True
                messages.success(request, f"✅ Invoice {invoice.number} saved successfully!")
                return redirect("preview_invoice")
            
            elif action == "download":
                # Save to database first, then download PDF
                if invoice_instance:
                    # Update existing invoice
                    invoice = invoice_instance
                    # Update fields from form
                    for field in form.cleaned_data:
                        setattr(invoice, field, form.cleaned_data[field])
                    # Delete old items
                    InvoiceItem.objects.filter(invoice=invoice_instance).delete()
                else:
                    # Create new invoice
                    invoice = form.save(commit=False)
                    if not invoice.number:
                        year = invoice.date.year if invoice.date else timezone.now().year
                        max_seq = Invoice.objects.filter(number__startswith=f"MO-{year}-").aggregate(
                            max_seq=Max("number"))["max_seq"]
                        if max_seq:
                            seq = int(max_seq.split("-")[-1]) + 1
                        else:
                            seq = 1
                        invoice.number = f"MO-{year}-{seq:02d}"
                
                invoice.subtotal = subtotal
                invoice.gst_total = gst_total
                invoice.grand_total = grand_total
                invoice.save()

                # Save items
                for item_data in items:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        description=item_data["description"],
                        quantity=item_data["quantity"],
                        unit_price=item_data["unit_price"],
                        gst_rate=item_data["gst_rate"]
                    )

                request.session["temp_invoice"]["number"] = invoice.number
                request.session["invoice_saved"] = True
                return redirect("export_invoice_pdf")

            return redirect("preview_invoice")
        else:
            messages.error(request, "Form errors - please check fields.")

    else:
        if invoice_instance:
            # Pre-populate form with existing data
            form = InvoiceForm(instance=invoice_instance)
        else:
            form = InvoiceForm()

    return render(request, "invoices/invoice_form.html", {
        "form": form,
        "existing_items": existing_items,
        "is_edit": invoice_instance is not None,
    })


@login_required
def preview_invoice(request):
    """Preview an invoice before exporting"""
    data = request.session.get("temp_invoice")
    if not data:
        messages.warning(request, "No data - create invoice first.")
        return redirect("create_invoice")
    
    # Convert date strings to date objects for display
    if data.get("date") and isinstance(data.get("date"), str):
        data["date"] = date.fromisoformat(data["date"])
    if data.get("due_date") and isinstance(data.get("due_date"), str):
        data["due_date"] = date.fromisoformat(data["due_date"])
    
    return render(request, "invoices/invoice_preview.html", {"invoice": data})


@login_required
def save_invoice_from_preview(request):
    """Save invoice from preview page if not already saved"""
    if request.method != "POST":
        return redirect("preview_invoice")
    
    # Check if already saved
    if request.session.get("invoice_saved"):
        messages.info(request, "Invoice already saved!")
        return redirect("preview_invoice")
    
    data = request.session.get("temp_invoice")
    if not data:
        messages.warning(request, "No data - create invoice first.")
        return redirect("create_invoice")
    
    # Save to database
    invoice = Invoice(
        customer_name=data["customer_name"],
        customer_abn=data["customer_abn"],
        customer_address=data["customer_address"],
        attention=data["attention"],
        po_reference=data["po_reference"],
        number=data["number"] if data["number"] != "DRAFT" else None,
        date=date.fromisoformat(data["date"]) if data.get("date") and isinstance(data["date"], str) else data.get("date"),
        due_date=date.fromisoformat(data["due_date"]) if data.get("due_date") and isinstance(data["due_date"], str) else data.get("due_date"),
        subtotal=Decimal(str(data["subtotal"])),
        gst_total=Decimal(str(data["gst_total"])),
        grand_total=Decimal(str(data["grand_total"]))
    )
    
    if not invoice.number:
        year = invoice.date.year if invoice.date else timezone.now().year
        max_seq = Invoice.objects.filter(number__startswith=f"MO-{year}-").aggregate(
            max_seq=Max("number"))["max_seq"]
        if max_seq:
            seq = int(max_seq.split("-")[-1]) + 1
        else:
            seq = 1
        invoice.number = f"MO-{year}-{seq:02d}"
    
    invoice.save()
    
    # Save items
    for item_data in data["items"]:
        InvoiceItem.objects.create(
            invoice=invoice,
            description=item_data["description"],
            quantity=Decimal(str(item_data["quantity"])),
            unit_price=Decimal(str(item_data["unit_price"])),
            gst_rate=Decimal(str(item_data["gst_rate"]))
        )
    
    request.session["temp_invoice"]["number"] = invoice.number
    request.session["invoice_saved"] = True
    messages.success(request, f"✅ Invoice {invoice.number} saved successfully!")
    
    return redirect("preview_invoice")


@login_required
def export_invoice_pdf(request):
    """Export invoice as PDF"""
    data = request.session.get("temp_invoice")
    if not data:
        return HttpResponse("No data.", status=400)

    # Convert date strings to date objects for template
    if isinstance(data.get("date"), str):
        data["date"] = date.fromisoformat(data["date"])
    if isinstance(data.get("due_date"), str):
        data["due_date"] = date.fromisoformat(data["due_date"])

    html_string = render(request, "invoices/invoice_preview.html", {"invoice": data}).content.decode("utf-8")
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="Tax_Invoice_{data["number"]}.pdf"'
    return response


# LIST VIEW
@login_required
def document_list(request):
    """List all invoices and estimates with cards"""
    invoices = Invoice.objects.all().order_by('-created_at')
    estimates = Estimate.objects.all().order_by('-created_at')
    
    # Combine into a single list with document type
    documents = []
    for inv in invoices:
        documents.append({
            'type': 'invoice',
            'id': inv.id,
            'number': inv.number,
            'customer_name': inv.customer_name,
            'date': inv.date,
            'total': inv.grand_total,
            'created_at': inv.created_at,
        })
    
    for est in estimates:
        documents.append({
            'type': 'estimate',
            'id': est.id,
            'number': est.number,
            'customer_name': est.customer_name,
            'date': est.date,
            'total': est.grand_total,
            'created_at': est.created_at,
        })
    
    # Sort by created_at descending
    documents.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render(request, "invoices/view_documents.html", {
        "documents": documents
    })


# OLD VIEWS FOR BACKWARD COMPATIBILITY (OPTIONAL)
@login_required
def create_document(request):
    """Legacy document creation view"""
    if request.method == "POST":
        form = DocumentForm(request.POST)
        if form.is_valid():
            item_count = int(request.POST.get("item_count", 0))
            items = []
            subtotal = Decimal("0")
            gst_total = Decimal("0")
            for i in range(item_count):
                prefix = f"item_{i}_"
                desc = request.POST.get(f"{prefix}description")
                if not desc:
                    continue
                qty = int(request.POST.get(f"{prefix}quantity", 1))
                unit_price = Decimal(request.POST.get(f"{prefix}unit_price", "0"))
                gst_rate = Decimal(request.POST.get(f"{prefix}gst_rate", "10"))
                line_sub = qty * unit_price
                line_gst = line_sub * (gst_rate / 100)
                items.append({
                    "description": desc,
                    "quantity": qty,
                    "unit_price": str(unit_price),
                    "gst_rate": str(gst_rate),
                    "amount": str(line_sub + line_gst),
                })
                subtotal += line_sub
                gst_total += line_gst
            grand_total = subtotal + gst_total
            data = {
                "doc_type": "invoice",
                "number": form.cleaned_data["number"],
                "date": form.cleaned_data["date"].isoformat() if form.cleaned_data["date"] else None,
                "due_date": form.cleaned_data["due_date"].isoformat() if form.cleaned_data["due_date"] else None,
                "customer_name": form.cleaned_data["customer_name"],
                "customer_abn": form.cleaned_data["customer_abn"],
                "customer_address": form.cleaned_data["customer_address"],
                "attention": form.cleaned_data["attention"],
                "po_reference": form.cleaned_data["po_reference"],
                "subtotal": str(subtotal),
                "gst_total": str(gst_total),
                "grand_total": str(grand_total),
                "items": items,
            }
            request.session["temp_document"] = data
            return redirect("preview_document")
    else:
        form = DocumentForm()
    return render(request, "invoices/form.html", {"form": form})


@login_required
def preview_document(request):
    """Legacy preview view"""
    data = request.session.get("temp_document")
    if not data:
        messages.warning(request, "No data - create document first.")
        return redirect("create_document")
    return render(request, "invoices/preview.html", {"document": data})


@login_required
def export_pdf(request):
    """Legacy PDF export"""
    data = request.session.get("temp_document")
    if not data:
        return HttpResponse("No data.", status=400)
    html_string = render(request, "invoices/preview.html", {"document": data}).content.decode("utf-8")
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    type_str = "Estimate" if data["doc_type"] == "estimate" else "Tax_Invoice"
    response['Content-Disposition'] = f'attachment; filename="{type_str}_{data["number"]}.pdf"'
    return response