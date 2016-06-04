from django.test import TestCase
from django_afip.templatetags.django_afip import format_cuit


class FormatCuitTagTestCase(TestCase):

    def test_good_string_input(self):
        self.assertEqual(
            format_cuit("20329642330"),
            "20-32964233-0"
        )
        self.assertEqual(
            format_cuit("20-32964233-0"),
            "20-32964233-0"
        )

    def test_good_numeric_input(self):
        self.assertEqual(
            format_cuit(20329642330),
            "20-32964233-0"
        )

    def test_bad_string_input(self):
        self.assertEqual(
            format_cuit("blah blah"),
            "blah blah"
        )

    def test_bad_numeric_input(self):
        self.assertEqual(
            format_cuit(1234),
            1234
        )
