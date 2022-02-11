import base64
import copy
from distutils.log import error
import docker
import unittest
from typing import Type
from botocore.exceptions import ClientError
from ecr_rigel_plugin import (
    __version__,
    DockerImageNotFoundError,
    DockerPushError,
    InvalidAWSCredentialsError,
    InvalidDockerImageNameError,
    InvalidImageRegistryError,
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

    @patch('ecr_rigel_plugin.ecr_rigel_plugin.aws_client')
    @patch('ecr_rigel_plugin.ecr_rigel_plugin.os.environ.get')
    def test_invalid_credentials_error(self, environ_mock: Mock, aws_mock: Mock) -> None:
        """
        Test if InvalidAWSCredentialsError is thrown if the AWS ECR credentials
        are not valid.
        """

        def stop(*args, **kwargs) -> None:
            raise ClientError(
                error_response=MagicMock(),
                operation_name=MagicMock()
            )

        environ_mock.return_value = 'test_value'
        aws_mock.side_effect = stop

        with self.assertRaises(InvalidAWSCredentialsError):
            plugin = Plugin(**self.base_plugin_data)
            plugin.authenticate(MagicMock())

    @patch('ecr_rigel_plugin.ecr_rigel_plugin.aws_client')
    @patch('ecr_rigel_plugin.ecr_rigel_plugin.os.environ.get')
    def test_token_decoding(self, environ_mock: Mock, aws_mock: Mock) -> None:
        """
        Test if AWS ECR token is properly decoded.
        """
        environ_mock.return_value = 'test_value'

        decoded_test_token = 'test_token'
        aws_ecr_mock = MagicMock()
        aws_ecr_mock.get_authorization_token.return_value = {
            'authorizationData': [
                {
                    'authorizationToken': base64.b64encode(f'AWS:{decoded_test_token}'.encode())
                }
            ]
        }
        aws_mock.return_value = aws_ecr_mock

        plugin = Plugin(**self.base_plugin_data)
        plugin.authenticate(MagicMock())

        self.assertEqual(plugin.token, decoded_test_token)

    @patch('ecr_rigel_plugin.ecr_rigel_plugin.aws_client')
    @patch('ecr_rigel_plugin.ecr_rigel_plugin.os.environ.get')
    def test_invalid_registry_error(self, environ_mock: Mock, aws_mock: Mock) -> None:
        """
        Test if InvalidImageRegistryError is thrown whenever
        an invalid registry is provided.
        """
        environ_mock.return_value = 'test_value'

        aws_ecr_mock = MagicMock()
        aws_ecr_mock.get_authorization_token.return_value = {
            'authorizationData': [
                {
                    'authorizationToken': base64.b64encode(f'AWS:test_token'.encode())
                }
            ]
        }
        aws_mock.return_value = aws_ecr_mock

        docker_client_mock = MagicMock()
        docker_client_mock.login.side_effect = docker.errors.APIError(message='Test error message.')

        with self.assertRaises(InvalidImageRegistryError) as context:
            plugin = Plugin(**self.base_plugin_data)
            plugin.authenticate(docker_client_mock)

        self.assertEqual(context.exception.kwargs['registry'], plugin.registry)

    def test_docker_push_error(self) -> None:
        """
        Test if DockerPushError is thrown if an error occurs while
        pushing Docker image.
        """
        error_message = 'Test error message.'

        docker_client_mock = MagicMock()
        docker_client_mock.push.return_value = [{'error': error_message}]

        with self.assertRaises(DockerPushError) as context:
            plugin = Plugin(**self.base_plugin_data)
            plugin.token = 'test_token'
            plugin.deploy(docker_client_mock)
        self.assertEqual(context.exception.kwargs['msg'], error_message)


if __name__ == '__main__':
    unittest.main()
