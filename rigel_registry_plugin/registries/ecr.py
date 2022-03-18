import base64
import os
from boto3 import client as aws_client
from boto3.exceptions import Boto3Error
from botocore.exceptions import BotoCoreError
from rigel_registry_plugin.exceptions import AWSBotoError
from pydantic import BaseModel, PrivateAttr
from rigelcore.clients import DockerClient
from rigelcore.exceptions import UndeclaredEnvironmentVariableError
from rigelcore.loggers import MessageLogger
from typing import Any


class AWSCredentials(BaseModel):
    """
    Personal credentials for AWS.

    :type access_key: string
    :ivar access_key: AWS access key.
    :type secret_access_key: string
    :ivar secret_access_key: AWS secret access key.
    """

    # List of required fields.
    access_key: str
    secret_access_key: str


class ECRPlugin(BaseModel):
    """
    A plugin for Rigel to deploy Docker images to AWS ECR.

    :type account: int
    :ivar account: AWS account identifier.
    :type credentials: AWSCredentials
    :ivar credentials: Personal credentials for AWS.
    :type docker_client: rigelcore.clients.DockerClient
    :ivar docker_client: A Docker client instance.
    :type image: string
    :ivar image: Desired name for the Docker image.
    :type logger: rigelcore.loggers.MessageLogger
    :ivar logger: A message logger.
    :type region: string
    :ivar region: AWS region.
    :type local_image: string
    :ivar local_image: Default name for the Docker image (OPTIONAL).
    :type user: string
    :ivar user: ECR user (OPTIONAL).
    """

    # List of required fields.
    account: int
    credentials: AWSCredentials
    image: str
    region: str

    # List of optional fields.
    local_image: str = 'rigel:temp'
    user: str = 'AWS'

    # List of private fields.
    _complete_image_name: str = PrivateAttr()
    _docker_client: DockerClient = PrivateAttr()
    _logger: MessageLogger = PrivateAttr()
    _registry: str = PrivateAttr()
    _token: str = PrivateAttr()

    def __init__(self, *args: Any, **kwargs: Any) -> None:

        self._docker_client = kwargs.pop('docker_client')
        self._logger = kwargs.pop('logger')

        super().__init__(*args, **kwargs)

        self._registry = f"{kwargs['account']}.dkr.ecr.{kwargs['region']}.amazonaws.com"
        self._complete_image_name = f"{self._registry}/{self.image}"

    def tag(self) -> None:
        """
        Tag existent Docker image to the desired tag.
        """
        self._docker_client.tag_image(
            self.local_image,
            self._complete_image_name
        )

    def authenticate(self) -> None:
        """
        Authenticate with AWS ECR.
        """
        def __get_env_var_value(env: str) -> str:
            """
            Retrieve a value stored in an environment variable.

            :type env: string
            :param env: Name of environment variable.
            :rtype: string
            :return: The value of the environment variable.
            """
            value = os.environ.get(env)
            if value is None:
                raise UndeclaredEnvironmentVariableError(env=env)
            return value

        try:

            # Obtain ECR authentication token.
            aws_ecr = aws_client(
                'ecr',
                aws_access_key_id=__get_env_var_value(self.credentials.access_key),
                aws_secret_access_key=__get_env_var_value(self.credentials.secret_access_key),
                region_name=self.region
            )

            # Decode ECR authentication token.
            encoded_token = aws_ecr.get_authorization_token()['authorizationData'][0]['authorizationToken']
            self._token = base64.b64decode(encoded_token).replace(b'AWS:', b'').decode('utf-8')

        except (Boto3Error, BotoCoreError) as exception:
            raise AWSBotoError(exception=exception)

        # Authenticate with AWS ECR.registry
        self._docker_client.login(self._registry, self.user, self._token)

    def deploy(self) -> None:
        """
        Deploy Docker image to AWS ECR.
        """
        self._docker_client.push_image(self._complete_image_name)

    def run(self) -> None:
        """
        Plugin entrypoint.
        """
        self.tag()
        self._logger.info(f"Created Docker image {self.image} from {self.local_image}.")

        self.authenticate()
        self._logger.info(f'Authenticated with AWS ECR ({self._registry}).')

        self.deploy()
        self._logger.info(f'Docker image {self._complete_image_name} was pushed with success to AWS ECR.')

    def stop(self) -> None:
        """
        Plugin graceful closing mechanism.
        """
        pass
