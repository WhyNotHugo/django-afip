"""Tests for provided template tags."""
from django_afip.templatetags.django_afip import format_cuit


def test_format_cuit_tag_with_string():
    """Test valid string inputs."""
    assert format_cuit("20329642330") == "20-32964233-0"
    assert format_cuit("20-32964233-0") == "20-32964233-0"


def test_format_cuit_tag_with_number():
    """Test valid numerical input."""
    assert format_cuit(20329642330) == "20-32964233-0"


def test_format_cuit_tag_with_bad_string():
    """Test invalid string input."""
    assert format_cuit("blah blah") == "blah blah"


def test_format_cuit_tag_with_bad_number():
    """Test invalid numerical input."""
    assert format_cuit(1234) == 1234
