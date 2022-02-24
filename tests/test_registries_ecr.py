import base64
import copy
import unittest
from botocore.exceptions import ClientError
from registry_rigel_plugin.exceptions import InvalidAWSCredentialsError
from registry_rigel_plugin.registries import ECRPlugin
from rigelcore.exceptions import UndeclaredEnvironmentVariableError
from typing import Dict, List
from unittest.mock import MagicMock, Mock, patch


class ECRPluginTesting(unittest.TestCase):
    """
    Test suite for the registry_rigel_plugin.registries.ECRPlugin class.
    """

    base_plugin_data = {
        'account': 123456789,
        'credentials': {
            'access_key': 'TEST_ACCESS_KEY',
            'secret_access_key': 'TEST_SECRET_ACCESS_KEY'
        },
        'image': 'test_image',
        'region': 'test_region',
        'local_image': 'test_local_image',

        # Injected fields.
        'docker_client': MagicMock(),
        'logger': MagicMock()
    }

    def test_tag_call(self) -> None:
        """
        Test if function 'tag' interfaces as expected with rigelcore.clients.DockerClient.
        """
        docker_mock = MagicMock()
        test_data = copy.deepcopy(self.base_plugin_data)
        test_data['docker_client'] = docker_mock

        plugin = ECRPlugin(*[], **test_data)
        plugin.tag()
        docker_mock.tag.assert_called_once_with(
            test_data['local_image'],
            "{}.dkr.ecr.{}.amazonaws.com/{}".format(
                test_data['account'],
                test_data['region'],
                test_data['image']
            )
        )

    @patch('registry_rigel_plugin.registries.ecr.os.environ.get')
    def test_undeclared_environment_variable_error(self, environ_mock: Mock) -> None:
        """
        Test if UndeclaredEnvironmentVariableError is thrown
        if an environment variable was left undeclared.
        """
        test_access_key = 'test_access_key'
        test_environ = {'TEST_ACCESS_KEY': test_access_key}

        environ_mock.side_effect = test_environ.get

        with self.assertRaises(UndeclaredEnvironmentVariableError) as context:
            plugin = ECRPlugin(*[], **self.base_plugin_data)
            plugin.authenticate()
        self.assertEqual(context.exception.kwargs['env'], 'TEST_SECRET_ACCESS_KEY')

    @patch('registry_rigel_plugin.registries.ecr.aws_client')
    @patch('registry_rigel_plugin.registries.ecr.os.environ.get')
    def test_invalid_credentials_error(self, environ_mock: Mock, aws_mock: Mock) -> None:
        """
        Test if InvalidAWSCredentialsError is thrown
        if the AWS ECR credentials are not valid.
        """

        def stop(*args: List[object], **kwargs: Dict[str, object]) -> None:
            raise ClientError(
                error_response=MagicMock(),
                operation_name=MagicMock()
            )

        environ_mock.return_value = 'test_value'
        aws_mock.side_effect = stop

        with self.assertRaises(InvalidAWSCredentialsError):
            plugin = ECRPlugin(*[], **self.base_plugin_data)
            plugin.authenticate()

    # TODO: finish testings.
    @patch('registry_rigel_plugin.registries.ecr.aws_client')
    @patch('registry_rigel_plugin.registries.ecr.os.environ.get')
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

        plugin = ECRPlugin(*[], **self.base_plugin_data)
        plugin.authenticate()

        self.assertEqual(plugin._token, decoded_test_token)

    def test_deploy_tag(self) -> None:
        """
        Ensure that 'deploy' function works as expected.
        """
        docker_mock = MagicMock()
        test_data = copy.deepcopy(self.base_plugin_data)
        test_data['docker_client'] = docker_mock

        plugin = ECRPlugin(*[], **test_data)
        plugin.deploy()

        docker_mock.push.assert_called_once_with(
            "{}.dkr.ecr.{}.amazonaws.com/{}".format(
                test_data['account'],
                test_data['region'],
                test_data['image']
            )
        )


if __name__ == '__main__':
    unittest.main()
