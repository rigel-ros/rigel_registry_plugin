from registry_rigel_plugin.exceptions import UnsupportedDockerRegistryError
from registry_rigel_plugin.registries import ECRPlugin, GenericDockerRegistryPlugin
from rigelcore.clients import DockerClient
from rigelcore.loggers import MessageLogger
from rigelcore.exceptions import MissingRequiredFieldError
from rigelcore.models import ModelBuilder
from typing import Any, Type


class Plugin:
    """
    A plugin for Rigel to deploy Docker images to Docker registries.
    """

    plugin_type: Type

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Select the proper plugin based on the specified registry.

        :type args: List[string, object]
        :param args: Required arguments for the plugin.
        :type kwargs: Dict[string, object]
        :param kwargs: Positional arguments for the plugin.
        """

        self.args: Any = args
        self.kwargs: Any = kwargs

        registry_name = kwargs.get('registry')
        if registry_name is None:
            raise MissingRequiredFieldError(field='registry')

        registry_name = registry_name.lower()
        if registry_name in ['gitlab', 'dockerhub']:
            self.plugin_type = GenericDockerRegistryPlugin

        elif registry_name == 'ecr':
            self.plugin_type = ECRPlugin

        else:
            raise UnsupportedDockerRegistryError(registry=registry_name)

        # Inject complex fields.
        self.kwargs['docker_client'] = DockerClient()
        self.kwargs['logger'] = MessageLogger()

    def run(self) -> None:
        """
        Delegate execution to adequate plugin.
        """
        builder = ModelBuilder(self.plugin_type)
        plugin = builder.build(self.args, self.kwargs)
        plugin.run()
