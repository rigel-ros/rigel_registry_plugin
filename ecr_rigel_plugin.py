import base64
import docker
import os
from boto3 import client as aws_client
from botocore.exceptions import ClientError
from dataclasses import dataclass, field
from rigel.loggers import DockerLogPrinter, MessageLogger
from typing import Dict


@dataclass
class Plugin:
    """
    A plugin for Rigel that deploys a Docker image to AWS ECR.

    :type account: int
    :param account: The AWS account ID.
    :type credentials: Dict[string, string]
    :param credentials: A dictionary containing the environment variables with access credentials.
    :type local_image: string
    :param local_image: The local name for the Docker image.
    :type image: string
    :param image: The desired name for the Docker image.
    :type region: strong
    :param region: The AWS region.
    :type user: string
    :param user: The ECR user (OPTIONAL).
    """

    account: int
    credentials: Dict[str, str]
    local_image: str
    image: str
    region: str

    user: str = field(default_factory=lambda: 'AWS')

    def __create_docker_client(self) -> docker.api.client.APIClient:
        """
        Create a Docker client instance.

        :rtype: docker.api.client.APIClient
        :return: A Docker client instance.
        """
        docker_host = os.environ.get('DOCKER_PATH')
        if docker_host:
            return docker.APIClient(base_url=docker_host)
        else:
            return docker.APIClient(base_url='unix:///var/run/docker.sock')

    def __post_init__(self) -> None:
        """
        Ensure that passed data is valid.
        """

        # Ensure no declared field was left undefined.
        for field_name, field_value in self.__dict__.items():
            if field_value is None:
                MessageLogger.error(f"Field '{field_name}' was declared but left undefined.")
                exit(1)

        # Ensure required credentials were provided.
        for credential in ['access_key', 'secret_access_key']:
            if self.credentials.get(credential) is None:
                MessageLogger.error(f"Missing credentials or invalid value.")
                exit(1)

        self.registry = f'{self.account}.dkr.ecr.{self.region}.amazonaws.com'

    def tag(self, docker_client: docker.api.client.APIClient) -> None:
        """
        Set the name of the existent Docker image.

        :type docker_client: docker.api.client.APIClient
        :param docker_client: A Docker client instance.
        """
        if ':' in self.image:
            new_image_name, new_image_tag = self.image.split(':')
        else:
            new_image_name = self.image
            new_image_tag = 'latest'

        docker_client.tag(
            image=self.local_image,
            repository=f'{self.registry}/{new_image_name}',
            tag=new_image_tag
        )

        MessageLogger.info(f"Set tag for Docker image {self.image} .")

    def authenticate(self, docker_client: docker.api.client.APIClient) -> None:
        """
        Authenticate in AWS ECR.

        :type docker_client: docker.api.client.APIClient
        :param docker_client: A Docker client instance.
        """
        try:

            # Obtain ECR authentication token
            aws_ecr = aws_client(
                'ecr',
                aws_access_key_id=os.environ.get(self.credentials['access_key']),
                aws_secret_access_key=os.environ.get(self.credentials['secret_access_key']),
                region_name=self.region
            )

            # Decode ECR authentication token
            token = aws_ecr.get_authorization_token()['authorizationData'][0]['authorizationToken']
            self.__token = base64.b64decode(token).replace(b'AWS:', b'').decode('utf-8')

        except ClientError:
            MessageLogger.error('Invalid AWS credentials.')
            exit(1)

        # Authenticate with AWS ECR.
        docker_client.login(
            username=self.user,
            password=self.__token,
            registry=self.registry
        )

        MessageLogger.info(f'Authenticated with AWS ECR ({self.registry}).')

    def deploy(self, docker_client: docker.api.client.APIClient) -> None:
        """
        Deploy image to AWS ECR.

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
                'password': self.__token
            }
        )

        printer = DockerLogPrinter()

        iterator = iter(image)
        while True:
            try:
                log = next(iterator)
                printer.log(log)

            except StopIteration:  # pushing operation finished
                if 'error' in log:
                    MessageLogger.error(f'An error occurred while pushing image {complete_image_name} to AWS ECR.')
                else:
                    MessageLogger.info(f'Image {complete_image_name} was pushed with success to AWS ECR.')
                break

            except ValueError:
                MessageLogger.warning(f'Unable to parse log message while pushing Docker image ({complete_image_name}): {log}')

    def run(self) -> None:
        """
        Plugin entry point.
        """
        docker_client = self.__create_docker_client()
        self.tag(docker_client)
        self.authenticate(docker_client)
        self.deploy(docker_client)
