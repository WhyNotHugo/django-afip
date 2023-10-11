from __future__ import annotations

from unittest import mock
from unittest.mock import patch

import pytest
from django.contrib import messages
from django.contrib.admin import site
from django.http import HttpRequest
from django.http import HttpResponse
from django.test import Client
from django.test import RequestFactory
from django.utils.translation import gettext as _
from factory.django import FileField
from pytest_django.asserts import assertContains
from pytest_django.asserts import assertNotContains

from django_afip import exceptions
from django_afip import factories
from django_afip import models
from django_afip.admin import ReceiptAdmin  # type: ignore[attr-defined]
from django_afip.admin import catch_errors  # type: ignore[attr-defined]


def test_certificate_expired() -> None:
    admin = mock.MagicMock()
    request = HttpRequest()

    with catch_errors(admin, request):
        raise exceptions.CertificateExpired

    assert admin.message_user.call_count == 1
    assert admin.message_user.call_args == mock.call(
        request,
        _("The AFIP Taxpayer certificate has expired."),
        messages.ERROR,
    )


def test_certificate_untrusted_cert() -> None:
    admin = mock.MagicMock()
    request = HttpRequest()

    with catch_errors(admin, request):
        raise exceptions.UntrustedCertificate

    assert admin.message_user.call_count == 1
    assert admin.message_user.call_args == mock.call(
        request,
        _("The AFIP Taxpayer certificate is untrusted."),
        messages.ERROR,
    )


def test_certificate_corrupt_cert() -> None:
    admin = mock.MagicMock()
    request = HttpRequest()

    with catch_errors(admin, request):
        raise exceptions.CorruptCertificate

    assert admin.message_user.call_count == 1
    assert admin.message_user.call_args == mock.call(
        request,
        _("The AFIP Taxpayer certificate is corrupt."),
        messages.ERROR,
    )


def test_certificate_auth_error() -> None:
    admin = mock.MagicMock()
    request = HttpRequest()

    with catch_errors(admin, request):
        raise exceptions.AuthenticationError

    assert admin.message_user.call_count == 1
    assert admin.message_user.call_args == mock.call(
        request,
        _("An unknown authentication error has ocurred: "),
        messages.ERROR,
    )


def test_without_key(admin_client: Client) -> None:
    taxpayer = factories.TaxPayerFactory(key=None)

    response = admin_client.post(
        "/admin/afip/taxpayer/",
        data={"_selected_action": [taxpayer.id], "action": "generate_key"},
        follow=True,
    )

    assert response.status_code == 200
    assert isinstance(response, HttpResponse)
    assertContains(response, "Key generated successfully.")

    taxpayer.refresh_from_db()
    assert "-----BEGIN PRIVATE KEY-----" in taxpayer.key.file.read().decode()


def test_with_key(admin_client: Client) -> None:
    taxpayer = factories.TaxPayerFactory(key=FileField(data=b"Blah"))

    response = admin_client.post(
        "/admin/afip/taxpayer/",
        data={"_selected_action": [taxpayer.id], "action": "generate_key"},
        follow=True,
    )

    assert response.status_code == 200
    assert isinstance(response, HttpResponse)
    assertContains(
        response,
        "No keys generated; Taxpayers already had keys.",
    )

    taxpayer.refresh_from_db()
    assert taxpayer.key.file.read().decode() == "Blah"


def test_admin_taxpayer_request_generation_with_csr(admin_client: Client) -> None:
    taxpayer = factories.TaxPayerFactory(key=None)
    taxpayer.generate_key()

    response = admin_client.post(
        "/admin/afip/taxpayer/",
        data={"_selected_action": [taxpayer.id], "action": "generate_csr"},
        follow=True,
    )

    assert response.status_code == 200
    assert (
        b"Content-Type: application/pkcs10" in response.serialize_headers().splitlines()
    )
    assert isinstance(response, HttpResponse)
    assertContains(response, "-----BEGIN CERTIFICATE REQUEST-----")


def test_admin_taxpayer_request_generation_without_key(admin_client: Client) -> None:
    taxpayer = factories.TaxPayerFactory(key=None)
    taxpayer.generate_key()

    response = admin_client.post(
        "/admin/afip/taxpayer/",
        data={"_selected_action": [taxpayer.id], "action": "generate_csr"},
        follow=True,
    )

    assert response.status_code == 200
    assert (
        b"Content-Type: application/pkcs10" in response.serialize_headers().splitlines()
    )
    assert isinstance(response, HttpResponse)
    assertContains(response, "-----BEGIN CERTIFICATE REQUEST-----")


def test_admin_taxpayer_request_generation_multiple_taxpayers(
    admin_client: Client,
) -> None:
    taxpayer1 = factories.TaxPayerFactory(key__data=b"Blah")
    taxpayer2 = factories.TaxPayerFactory(key__data=b"Blah", cuit="20401231230")

    response = admin_client.post(
        "/admin/afip/taxpayer/",
        data={
            "_selected_action": [taxpayer1.id, taxpayer2.id],
            "action": "generate_csr",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert isinstance(response, HttpResponse)
    assertContains(response, "Can only generate CSR for one taxpayer at a time")


def test_validation_filters(admin_client: Client) -> None:
    """Test the admin validation filters.

    This filters receipts by the validation status.
    """
    validated_receipt = factories.ReceiptFactory()
    failed_validation_receipt = factories.ReceiptFactory()
    not_validated_receipt = factories.ReceiptFactory()

    factories.ReceiptValidationFactory(receipt=validated_receipt)
    factories.ReceiptValidationFactory(
        result=models.ReceiptValidation.RESULT_REJECTED,
        receipt=failed_validation_receipt,
    )

    response = admin_client.get("/admin/afip/receipt/?status=validated")

    assert isinstance(response, HttpResponse)
    assertContains(
        response,
        '<input class="action-select" name="_selected_action" value="{}" '
        'type="checkbox">'.format(validated_receipt.pk),
        html=True,
    )
    assertNotContains(
        response,
        '<input class="action-select" name="_selected_action" value="{}" '
        'type="checkbox">'.format(not_validated_receipt.pk),
        html=True,
    )
    assertNotContains(
        response,
        '<input class="action-select" name="_selected_action" value="{}" '
        'type="checkbox">'.format(failed_validation_receipt.pk),
        html=True,
    )

    response = admin_client.get("/admin/afip/receipt/?status=not_validated")
    assertNotContains(
        response,
        '<input class="action-select" name="_selected_action" value="{}" '
        'type="checkbox">'.format(validated_receipt.pk),
        html=True,
    )
    assert isinstance(response, HttpResponse)
    assertContains(
        response,
        '<input class="action-select" name="_selected_action" value="{}" '
        'type="checkbox">'.format(not_validated_receipt.pk),
        html=True,
    )
    assertContains(
        response,
        '<input class="action-select" name="_selected_action" value="{}" '
        'type="checkbox">'.format(failed_validation_receipt.pk),
        html=True,
    )


@pytest.mark.django_db()
def test_receipt_admin_get_exclude() -> None:
    admin = ReceiptAdmin(models.Receipt, site)
    request = RequestFactory().get("/admin/afip/receipt")
    request.user = factories.UserFactory()

    assert "related_receipts" in admin.get_fields(request)


@pytest.mark.django_db()
def test_receipt_pdf_factories_and_files() -> None:
    with_file = factories.ReceiptPDFWithFileFactory()
    without_file = factories.ReceiptPDFFactory()

    assert not without_file.pdf_file
    assert with_file.pdf_file


def test_has_file_filter_all(admin_client: Client) -> None:
    """Check that the has_file filter applies properly

    In order to confirm that it's working, we check that the link to the
    object's change page is present, since no matter how we reformat the rows,
    this will always be present as long as the object is listed.
    """
    with_file = factories.ReceiptPDFWithFileFactory()
    without_file = factories.ReceiptPDFFactory()

    response = admin_client.get("/admin/afip/receiptpdf/")
    assert isinstance(response, HttpResponse)
    assertContains(response, f"/admin/afip/receiptpdf/{with_file.pk}/change/")
    assertContains(response, f"/admin/afip/receiptpdf/{without_file.pk}/change/")


def test_has_file_filter_with_file(admin_client: Client) -> None:
    with_file = factories.ReceiptPDFWithFileFactory()
    without_file = factories.ReceiptPDFFactory()

    response = admin_client.get("/admin/afip/receiptpdf/?has_file=yes")
    assert isinstance(response, HttpResponse)
    assertContains(response, f"/admin/afip/receiptpdf/{with_file.pk}/change/")
    assertNotContains(response, f"/admin/afip/receiptpdf/{without_file.pk}/change/")


def test_has_file_filter_without_file(admin_client: Client) -> None:
    with_file = factories.ReceiptPDFWithFileFactory()
    without_file = factories.ReceiptPDFFactory()

    response = admin_client.get("/admin/afip/receiptpdf/?has_file=no")
    assert isinstance(response, HttpResponse)
    assertNotContains(response, f"/admin/afip/receiptpdf/{with_file.pk}/change/")
    assertContains(response, f"/admin/afip/receiptpdf/{without_file.pk}/change/")


def test_validate_certs_action_success(admin_client: Client) -> None:
    receipt = factories.ReceiptFactory()

    with patch(
        "django_afip.models.ReceiptQuerySet.validate", spec=True, return_value=[]
    ) as validate:
        response = admin_client.post(
            "/admin/afip/receipt/",
            data={"_selected_action": [receipt.id], "action": "validate"},
            follow=True,
        )

    assert response.status_code == 200
    assert validate.call_count == 1
    assert list(response.context["messages"]) == []


def test_validate_certs_action_errors(admin_client: Client) -> None:
    receipt = factories.ReceiptFactory()

    with patch(
        "django_afip.models.ReceiptQuerySet.validate",
        spec=True,
        return_value=["Something went wrong"],
    ) as validate:
        response = admin_client.post(
            "/admin/afip/receipt/",
            data={"_selected_action": [receipt.id], "action": "validate"},
            follow=True,
        )

    assert response.status_code == 200
    assert validate.call_count == 1

    messages = list(response.context["messages"])
    assert len(messages) == 1

    message = messages[0].message
    assert message == "Receipt validation failed: ['Something went wrong']."


def test_admin_fetch_points_of_sales(admin_client: Client) -> None:
    taxpayer1 = factories.TaxPayerFactory()
    taxpayer2 = factories.TaxPayerFactory(cuit="20401231230")
    with patch(
        "django_afip.models.TaxPayer.fetch_points_of_sales",
        spec=True,
        return_value=[("dummy-point-of-sales", True), ("another", False)],
    ):
        response = admin_client.post(
            "/admin/afip/taxpayer/",
            data={
                "_selected_action": [taxpayer1.id, taxpayer2.id],
                "action": "fetch_points_of_sales",
            },
            follow=True,
        )

    assert response.status_code == 200

    messages = [msg.message for msg in list(response.context["messages"])]
    assert len(messages) == 2

    assert "2 points of sales already existed." in messages
    assert "2 points of sales created." in messages
