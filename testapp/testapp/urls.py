from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.static import serve

from django_afip import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "invoices/pdf/<int:pk>",
        views.ReceiptPDFView.as_view(),
        name="receipt_displaypdf_view",
    ),
    path(
        "invoices/pdf/<int:pk>",
        views.ReceiptPDFDownloadView.as_view(),
        name="receipt_pdf_view",
    ),
    path(
        "media/<path>",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
