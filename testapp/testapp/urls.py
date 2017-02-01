"""testapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.static import serve

from django_afip import views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(
        r'^invoices/pdf/(?P<pk>\d+)$',
        views.ReceiptPDFView.as_view(),
        name='receipt_pdf_view',
    ),
    url(
        r'^invoices/html/(?P<pk>\d+)$',
        views.ReceiptHTMLView.as_view(),
        name='receipt_html_view',
    ),
    url(
        r'^media/(?P<path>.*)$',
        serve,
        {'document_root': settings.MEDIA_ROOT},
    ),
]
