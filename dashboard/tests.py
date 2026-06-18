from django.test import TestCase

# Create your tests here.


class BasicInstallationTests(TestCase):

    def test_that_unit_testing_is_able_to_start(self):
        """
        The most basic test is whether or not your testing
        can even begin.
        """
        self.assertEqual(True, True)
