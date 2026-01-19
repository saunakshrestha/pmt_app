from decimal import Decimal
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Max
from weasyprint import HTML
from .forms import DocumentForm
from .models import Document, Item


def create_document(request):
    if request.method == "POST":
        form = DocumentForm(request.POST)
        if form.is_valid():
            # Collect items
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

            # Session data for preview
            data = {
                "doc_type": form.cleaned_data["doc_type"],
                "number": form.cleaned_data["number"],
                "date": form.cleaned_data["date"].isoformat() if form.cleaned_data["date"] else None,
                "valid_until": form.cleaned_data["valid_until"].isoformat() if form.cleaned_data["valid_until"] else None,
                "due_date": form.cleaned_data["due_date"].isoformat() if form.cleaned_data["due_date"] else None,
                "customer_name": form.cleaned_data["customer_name"],
                "customer_abn": form.cleaned_data["customer_abn"],
                "customer_address": form.cleaned_data["customer_address"],
                "attention": form.cleaned_data["attention"],
                "po_reference": form.cleaned_data["po_reference"],
                "summary": form.cleaned_data["summary"],  # list
                "terms_conditions": form.cleaned_data["terms_conditions"],
                "payment_terms": form.cleaned_data["payment_terms"],
                "subtotal": str(subtotal),
                "gst_total": str(gst_total),
                "grand_total": str(grand_total),
                "items": items,
            }
            request.session["temp_document"] = data

            action = request.POST.get("action")
            if action == "save":
                doc = form.save(commit=False)
                if not doc.number:
                    if doc.doc_type == "estimate":
                        max_num = Document.objects.filter(doc_type="estimate").aggregate(max_num=Max("number"))["max_num"] or "2025000"
                        doc.number = str(int(max_num) + 1)
                    else:
                        year = doc.date.year
                        max_seq = Document.objects.filter(doc_type="invoice", number__startswith=f"MO-{year}-").aggregate(max_seq=Max("number"))["max_seq"] or f"MO-{year}-00"
                        seq = int(max_seq.split("-")[-1]) + 1
                        doc.number = f"MO-{year}-{seq:02d}"
                doc.subtotal = subtotal
                doc.gst_total = gst_total
                doc.grand_total = grand_total
                doc.save()

                # Save items
                for item_data in items:
                    Item.objects.create(
                        document=doc,
                        description=item_data["description"],
                        quantity=item_data["quantity"],
                        unit_price=item_data["unit_price"],
                        gst_rate=item_data["gst_rate"]
                    )

                request.session["temp_document"]["number"] = doc.number  # Update session with generated number
                messages.success(request, f"Saved {doc.doc_type.title()} {doc.number}")

            return redirect("preview_document")
        else:
            messages.error(request, "Form errors - please check fields.")

    else:
        form = DocumentForm()

    return render(request, "invoices/form.html", {"form": form})


def preview_document(request):
    data = request.session.get("temp_document")
    if not data:
        messages.warning(request, "No data - create document first.")
        return redirect("create_document")
    return render(request, "invoices/preview.html", {"document": data})


def export_pdf(request):
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


def document_list(request):
    docs = Document.objects.all()
    return render(request, "invoices/list.html", {"documents": docs})