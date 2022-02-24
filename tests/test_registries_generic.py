import copy
import unittest
from rigel_registry_plugin.registries import GenericDockerRegistryPlugin
from rigelcore.exceptions import UndeclaredEnvironmentVariableError
from unittest.mock import MagicMock, Mock, patch


class GenericDockerRegistryPluginTesting(unittest.TestCase):
    """
    Test suite for the rigel_registry_plugin.registries.GenericDockerRegistryPlugin class.
    """

    base_plugin_data = {
        'credentials': {
            'username': 'TEST_USERNAME',
            'password': 'TEST_PASSWORD'
        },
        'image': 'test_image',
        'local_image': 'test_local_image',
        'registry': 'test_registry',

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

        plugin = GenericDockerRegistryPlugin(*[], **test_data)
        plugin.tag()
        docker_mock.tag.assert_called_once_with(
            test_data['local_image'],
            f"{test_data['registry']}/{test_data['image']}"
        )

    @patch('rigel_registry_plugin.registries.generic.os.environ.get')
    def test_undeclared_environment_variable_error(self, environ_mock: Mock) -> None:
        """
        Test if UndeclaredEnvironmentVariableError is thrown
        if an environment variable was left undeclared.
        """
        test_username = 'test_username'
        test_environ = {'TEST_USERNAME': test_username}

        environ_mock.side_effect = test_environ.get

        with self.assertRaises(UndeclaredEnvironmentVariableError) as context:
            plugin = GenericDockerRegistryPlugin(*[], **self.base_plugin_data)
            plugin.authenticate()
        self.assertEqual(context.exception.kwargs['env'], 'TEST_PASSWORD')

    @patch('rigel_registry_plugin.registries.generic.os.environ.get')
    def test_authenticate_call(self, environ_mock: Mock) -> None:
        """
        Test if function 'authenticate' interfaces as expected
        with rigelcore.clients.DockerClient class.
        """
        docker_mock = MagicMock()
        test_data = copy.deepcopy(self.base_plugin_data)
        test_data['docker_client'] = docker_mock

        test_username = 'test_username'
        test_password = 'test_password'
        test_environ = {'TEST_USERNAME': test_username, 'TEST_PASSWORD': test_password}
        environ_mock.side_effect = test_environ.get

        plugin = GenericDockerRegistryPlugin(*[], **test_data)
        plugin.authenticate()
        docker_mock.login.assert_called_once_with(
            test_data['registry'],
            test_username,
            test_password
        )

    def test_push_call(self) -> None:
        """
        Test if function 'deploy' interfaces as expected with rigelcore.clients.DockerClient.
        """
        docker_mock = MagicMock()
        test_data = copy.deepcopy(self.base_plugin_data)
        test_data['docker_client'] = docker_mock

        plugin = GenericDockerRegistryPlugin(*[], **test_data)
        plugin.deploy()
        docker_mock.push.assert_called_once_with(
            f"{test_data['registry']}/{test_data['image']}"
        )


if __name__ == '__main__':
    unittest.main()
