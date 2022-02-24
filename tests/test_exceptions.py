import unittest
from registry_rigel_plugin.exceptions import (
    InvalidAWSCredentialsError,
    UnsupportedDockerRegistryError
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

    def test_unsupported_docker_registry_error(self) -> None:
        """
        Ensure that instances of UnsupportedDockerRegistryError are thrown as expected.
        """
        test_registry = 'test_registry'
        err = UnsupportedDockerRegistryError(registry=test_registry)
        self.assertEqual(err.code, 51)
        self.assertEqual(err.kwargs['registry'], test_registry)


if __name__ == '__main__':
    unittest.main()
