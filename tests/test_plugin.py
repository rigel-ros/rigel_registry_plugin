import copy
import docker
import unittest
from ecr_rigel_plugin import (
    __version__,
    InvalidDockerImageNameError,
    DockerImageNotFoundError,
    UndefinedEnvironmentVariableError,
    Plugin
)
from rigel.exceptions import MissingRequiredFieldError
from unittest.mock import MagicMock, Mock, patch

class PluginTesting(unittest.TestCase):

    base_plugin_data = {
        'account': 'test_acount',
        'image': 'test_image',
        'local_image': 'test_local_image',
        'region': 'test_region',
        'credentials': {
            'access_key': 'TEST_ACCESS_KEY',
            'secret_access_key': 'TEST_SECRET_ACCESS_KEY'
        },
    }

    def test_version(self) -> None:
        """
        Basic test to ensure that plugin version is as expected.
        """
        self.assertEqual(__version__, '0.1.0')

    def test_run_exists(self) -> None:
        """
        Ensure that Plugin class has required 'run' function.
        """
        self.assertTrue('run' in Plugin.__dict__)

    def test_missing_credentials_access_key(self) -> None:
        """
        Test if MissingRequiredFieldError is thrown if credentials['access_key'] is not defined.
        """
        plugin_data = copy.deepcopy(self.base_plugin_data)
        plugin_data['credentials'].pop('access_key')
        with self.assertRaises(MissingRequiredFieldError) as context:
            Plugin(**plugin_data)
        self.assertEqual(context.exception.kwargs['field'], 'credentials[access_key]')

    def test_missing_credentials_access_key(self) -> None:
        """
        Test if MissingRequiredFieldError is thrown if credentials['secret_access_key'] is not defined.
        """
        plugin_data = copy.deepcopy(self.base_plugin_data)
        plugin_data['credentials'].pop('secret_access_key')
        with self.assertRaises(MissingRequiredFieldError) as context:
            Plugin(**plugin_data)
        self.assertEqual(context.exception.kwargs['field'], 'credentials[secret_access_key]')

    def test_tag_invalid_image_name_error(self) -> None:
        """
        Test if InvalidDockerImageNameError is thrown an invalid Docker image name is provided.
        """
        image = 'invalid:image:name'

        plugin_data = copy.deepcopy(self.base_plugin_data)
        plugin_data['image'] = image

        with self.assertRaises(InvalidDockerImageNameError) as context:
            plugin = Plugin(**plugin_data)
            plugin.tag(MagicMock())
        self.assertEqual(context.exception.kwargs['image'], image)

    def test_tag_image_not_found_error(self) -> None:
        """
        Test if DockerImageNotFoundError is thrown if image to be tagged does not exist.
        """
        image = 'unknown_image:latest'

        plugin_data = copy.deepcopy(self.base_plugin_data)
        plugin_data['image'] = image

        docker_client_mock = MagicMock()
        docker_client_mock.tag.side_effect = docker.errors.ImageNotFound(message='Test error.')

        with self.assertRaises(DockerImageNotFoundError) as context:
            plugin = Plugin(**plugin_data)
            plugin.tag(docker_client_mock)
        self.assertEqual(context.exception.kwargs['image'], image)

    @patch('ecr_rigel_plugin.ecr_rigel_plugin.aws_client')
    @patch('ecr_rigel_plugin.ecr_rigel_plugin.os.environ.get')
    def test_undefined_env_var_error(self, environ_mock: Mock, aws_mock: Mock) -> None:
        """
        Test if UndefinedEnvironmentVariableError is thrown if an
        environment variable was left undeclared.
        """
        test_access_key = 'test_access_key'
        test_environ = {'TEST_ACCESS_KEY': test_access_key}

        environ_mock.side_effect = test_environ.get

        with self.assertRaises(UndefinedEnvironmentVariableError) as context:
            plugin = Plugin(**self.base_plugin_data)
            plugin.authenticate(MagicMock())
        self.assertEqual(context.exception.kwargs['var'], 'TEST_SECRET_ACCESS_KEY')



if __name__ == '__main__':
    unittest.main()
