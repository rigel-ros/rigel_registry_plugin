from rigelcore.exceptions import RigelError


class InvalidAWSCredentialsError(RigelError):
    """
    Raised whenever an attempt is made to authenticate with AWS ECR using invalid access credentials.
    """
    base = "Invalid AWS access credentials. Unable to authenticate with AWS ECR."
    code = 50


class UnsupportedDockerRegistryError(RigelError):
    """
    Raised whenever an attempt is made to deploy a Docker image to an unsupported registry.

    :type registry: string
    :ivar registry: The unsupported registry.
    """
    base = "Plugin does not support registry {registry}."
    code = 51
