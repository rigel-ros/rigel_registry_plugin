import inspect
import unittest
from registry_rigel_plugin import Plugin
from registry_rigel_plugin.registries import (
    ECRPlugin,
    GenericDockerRegistryPlugin
)
from unittest.mock import MagicMock, Mock, patch


class PluginTesting(unittest.TestCase):
    """
    Test suite for the registry_rigel_plugin.Plugin class.
    """

    def test_compliant(self) -> None:
        """
        Ensure that Plugin class has required 'run' function.
        """
        self.assertTrue('run' in Plugin.__dict__)

        signature = inspect.signature(Plugin.run)
        self.assertEqual(len(signature.parameters), 1)

    def test_ecr_plugin_choice(self) -> None:
        """
        Ensure that plugin type registry_rigel_plugin.registries.ECRPlugin
        is selected if 'ecr' is specified.
        """
        plugin = Plugin(*[], **{'registry': 'ecr'})
        self.assertEqual(plugin.plugin_type, ECRPlugin)

    def test_generic_plugin_choice_gitlab(self) -> None:
        """
        Ensure that plugin type registry_rigel_plugin.registries.GenericDockerRegistryPlugin
        is selected if 'gitlab' is specified.
        """
        plugin = Plugin(*[], **{'registry': 'gitlab'})
        self.assertEqual(plugin.plugin_type, GenericDockerRegistryPlugin)

    def test_generic_plugin_choice_dockerhub(self) -> None:
        """
        Ensure that plugin type registry_rigel_plugin.registries.GenericDockerRegistryPlugin
        is selected if 'dockerhub' is specified.
        """
        plugin = Plugin(*[], **{'registry': 'dockerhub'})
        self.assertEqual(plugin.plugin_type, GenericDockerRegistryPlugin)

    @patch('registry_rigel_plugin.plugin.ModelBuilder')
    def test_plugin_run_function_call(self, builder_mock: Mock) -> None:
        """
        Ensure that if execution is properly delegated to the 'run' function of the selected plugin.
        """
        test_args = [1, 2, 3]
        test_kwargs = {'registry': 'gitlab', 'test_key': 'test_value'}

        plugin_mock = MagicMock()

        builder_instance_mock = MagicMock()
        builder_instance_mock.build.return_value = plugin_mock
        builder_mock.return_value = builder_instance_mock

        plugin = Plugin(*test_args, **test_kwargs)
        plugin.run()

        builder_mock.assert_called_once_with(plugin.plugin_type)
        builder_instance_mock.build.assert_called_once_with(plugin.args, plugin.kwargs)
        plugin_mock.run.assert_called_once()


if __name__ == '__main__':
    unittest.main()
