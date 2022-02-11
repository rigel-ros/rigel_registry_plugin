import base64
import docker
import os
from .exceptions import (
    DockerImageNotFoundError,
    DockerPushError,
    InvalidAWSCredentialsError,
    InvalidDockerImageNameError,
    InvalidImageRegistryError,
    UndefinedEnvironmentVariableError
)
from boto3 import client as aws_client
from botocore.exceptions import ClientError
from dataclasses import dataclass, field
from rigel.exceptions import (
    MissingRequiredFieldError,
)
from rigel.loggers import DockerLogPrinter, MessageLogger
from typing import Dict


def create_docker_client() -> docker.api.client.APIClient:  # pragma: no cover
    """
    Create a Docker client instance.

    :rtype: docker.api.client.APIClient
    :return: A Docker client instance.
    """
    return docker.from_env().api


@dataclass
class Plugin:
    """
    A plugin for Rigel to deploy Docker images to AWS ECR.

    :type account: int
    :ivar account: AWS account identifier.
    :type credentials: Dict[string, string]
    :ivar credentials: Dictionary of environment variables with access credentials' values.
    :type image: string
    :ivar image: Desired name for the Docker image.
    :type region: string
    :ivar region: AWS region.
    :type registry: string
    :ivar registry: ECR registry.
    :type local_image: string
    :ivar local_image: Default name for the Docker image (OPTIONAL).
    :type user: string
    :ivar user: ECR user (OPTIONAL).
    """

    # List of required fields.
    account: int
    credentials: Dict[str, str]
    image: str
    region: str

    # List of optional fields.
    local_image: str = field(default_factory=lambda: 'rigel:temp')
    user: str = field(default_factory=lambda: 'AWS')

    def __get_env_var_value(self, var: str) -> str:
        """
        Retrieve a value stored in an environment variable.

        :type var: string
        :param var: Name of environment variable.
        :rtype: string
        :return: The value of the environment variable.
        """
        value = os.environ.get(var)
        if value is None:
            raise UndefinedEnvironmentVariableError(var=var)
        return value

    def __post_init__(self) -> None:
        """
        Ensure that provided data is valid.
        """

        # NOTE: there's no need to check for undeclared fields
        # as the main Rigelfile parser already does that.

        # Ensure required credentials were provided.
        for credential in ['access_key', 'secret_access_key']:
            if self.credentials.get(credential) is None:
                raise MissingRequiredFieldError(field=f"credentials[{credential}]")

        # 'Registry' field can now be infered from existing data.
        self.registry = f'{self.account}.dkr.ecr.{self.region}.amazonaws.com'

    def tag(self, docker_client: docker.api.client.APIClient) -> None:
        """
        Tag existent Docker image to the desired tag.

        :type docker_client: docker.api.client.APIClient
        :param docker_client: A Docker client instance.
        """
        if ':' in self.image:
            try:
                desired_image_name, desired_image_tag = self.image.split(':')
            except ValueError:
                raise InvalidDockerImageNameError(image=self.image)
        else:
            desired_image_name = self.image
            desired_image_tag = 'latest'

        try:
            print(docker_client)
            docker_client.tag(
                image=self.local_image,
                repository=f'{self.registry}/{desired_image_name}',
                tag=desired_image_tag
            )
        except docker.errors.ImageNotFound:
            raise DockerImageNotFoundError(image=self.image)

        MessageLogger.info(f"Changed Docker image tag to '{self.local_image}'.")

    def authenticate(self, docker_client: docker.api.client.APIClient) -> None:
        """
        Authenticate with AWS ECR.

        :type docker_client: docker.api.client.APIClient
        :param docker_client: A Docker client instance.
        """
        try:

            # Obtain ECR authentication token.
            aws_ecr = aws_client(
                'ecr',
                aws_access_key_id=self.__get_env_var_value(self.credentials['access_key']),
                aws_secret_access_key=self.__get_env_var_value(self.credentials['secret_access_key']),
                region_name=self.region
            )

            # Decode ECR authentication token.
            encoded_token = aws_ecr.get_authorization_token()['authorizationData'][0]['authorizationToken']
            self.token = base64.b64decode(encoded_token).replace(b'AWS:', b'').decode('utf-8')

        except ClientError:
            raise InvalidAWSCredentialsError()

        # Authenticate with AWS ECR.
        try:
            docker_client.login(
                username=self.user,
                password=self.token,
                registry=self.registry
            )
        except docker.errors.APIError:
            raise InvalidImageRegistryError(registry=self.registry)

        MessageLogger.info(f'Authenticated with AWS ECR ({self.registry}).')

    def deploy(self, docker_client: docker.api.client.APIClient) -> None:
        """
        Deploy Docker image to AWS ECR.

        :type docker_client: docker.api.client.APIClient
        :param docker_client: A Docker client instance.
        """
        complete_image_name = f'{self.registry}/{self.image}'

        image = docker_client.push(
            complete_image_name,
            stream=True,
            decode=True,
            auth_config={
                'username': self.user,
                'password': self.token
            }
        )

        printer = DockerLogPrinter()

        iterator = iter(image)
        while True:

            try:

                log = next(iterator)
                printer.log(log)

            except StopIteration:

                if 'error' in log:
                    raise DockerPushError(msg=log['error'])
                else:
                    MessageLogger.info(f'Image {complete_image_name} was pushed with success to AWS ECR.')
                break

            except ValueError:
                MessageLogger.warning(f'Unable to parse log message: {log}')

    def run(self) -> None:
        """
        Plugin entry point.
        """
        docker_client = create_docker_client()
        self.tag(docker_client)
        self.authenticate(docker_client)
        self.deploy(docker_client)
