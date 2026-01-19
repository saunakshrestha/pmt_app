from django.urls import path
from invoices.views import create_document, preview_document, export_pdf, document_list

urlpatterns = [
    path('', create_document, name='create_document'),
    path('preview/', preview_document, name='preview_document'),
    path('pdf/', export_pdf, name='export_pdf'),
    path('list/', document_list, name='document_list'),
]