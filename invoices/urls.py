from django.urls import path
from invoices import views

urlpatterns = [
    # Portal Home
    path('', views.invoices_home, name='invoices_home'),
    
    # Estimate URLs
    path('estimate/create/', views.create_estimate, name='create_estimate'),
    path('estimate/edit/<int:estimate_id>/', views.create_estimate, name='edit_estimate'),
    path('estimate/preview/', views.preview_estimate, name='preview_estimate'),
    path('estimate/save/', views.save_estimate_from_preview, name='save_estimate_from_preview'),
    path('estimate/pdf/', views.export_estimate_pdf, name='export_estimate_pdf'),
    
    # Invoice URLs
    path('invoice/create/', views.create_invoice, name='create_invoice'),
    path('invoice/edit/<int:invoice_id>/', views.create_invoice, name='edit_invoice'),
    path('invoice/preview/', views.preview_invoice, name='preview_invoice'),
    path('invoice/save/', views.save_invoice_from_preview, name='save_invoice_from_preview'),
    path('invoice/pdf/', views.export_invoice_pdf, name='export_invoice_pdf'),
    
    # List view
    path('documents/', views.document_list, name='document_list'),
    
    # Legacy URLs (for backward compatibility)
    path('create/', views.create_document, name='create_document'),
    path('preview/', views.preview_document, name='preview_document'),
    path('pdf/', views.export_pdf, name='export_pdf'),
]