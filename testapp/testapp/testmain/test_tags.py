"""Tests for provided template tags."""
from django.test import TestCase

from django_afip.templatetags.django_afip import format_cuit


class FormatCuitTagTestCase(TestCase):
    """Test the format_cuit tag."""

    def test_good_string_input(self):
        """Test valid string inputs."""
        self.assertEqual(
            format_cuit('20329642330'),
            '20-32964233-0'
        )
        self.assertEqual(
            format_cuit('20-32964233-0'),
            '20-32964233-0'
        )

    def test_good_numeric_input(self):
        """Test valid numerical input."""
        self.assertEqual(
            format_cuit(20329642330),
            '20-32964233-0'
        )

    def test_bad_string_input(self):
        """Test invalid string input."""
        self.assertEqual(
            format_cuit('blah blah'),
            'blah blah'
        )

    def test_bad_numeric_input(self):
        """Test invalid numerical input."""
        self.assertEqual(
            format_cuit(1234),
            1234
        )
