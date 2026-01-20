from django.contrib import admin
from .models import Estimate, EstimateItem, Invoice, InvoiceItem


class EstimateItemInline(admin.TabularInline):
    model = EstimateItem
    extra = 1


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Estimate)
class EstimateAdmin(admin.ModelAdmin):
    list_display = ['number', 'customer_name', 'date', 'valid_until', 'grand_total', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['number', 'customer_name', 'customer_abn']
    inlines = [EstimateItemInline]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['number', 'customer_name', 'date', 'due_date', 'grand_total', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['number', 'customer_name', 'customer_abn', 'po_reference']
    inlines = [InvoiceItemInline]


