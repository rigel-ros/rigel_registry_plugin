import unittest
from rigel_registry_plugin.exceptions import (
    InvalidAWSCredentialsError,
)


class ExceptionTesting(unittest.TestCase):
    """
    Test suite for all classes under ecr_rigel_plugin.exceptions.
    """

    def test_invalid_aws_credentials_error(self) -> None:
        """
        Ensure that instances of InvalidAWSCredentialsError are thrown as expected.
        """
        err = InvalidAWSCredentialsError()
        self.assertEqual(err.code, 50)


if __name__ == '__main__':
    unittest.main()
