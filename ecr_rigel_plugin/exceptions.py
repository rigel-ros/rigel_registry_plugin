from rigel.exceptions import RigelError


class DockerImageNotFoundError(RigelError):
    """
    Raised whenever an attempt is made to tag a Docker image that does not exist.

    :type image: string
    :ivar image: Name of unexisting Docker image.
    """
    base = "Docker image {image} was not found."
    code = 50


class InvalidDockerImageNameError(RigelError):
    """
    Raised whenever an attempt is made to tag a Docker image using an invalid image name.

    :type image: string
    :ivar image: Invalid Docker image name.
    """
    base = "Invalid Docker image name '{image}'."
    code = 51


class InvalidAWSCredentialsError(RigelError):
    """
    Raised whenever an attempt is made to authenticate with AWS ECR using invalid access credentials.
    """
    base = "Invalid AWS access credentials. Unable to authenticate with AWS ECR."
    code = 52


class UndefinedEnvironmentVariableError(RigelError):
    """
    Raised whenever an attempt is made to authenticate with AWS ECR using invalid access credentials.

    :type var: string
    :ivar var: Name of undefined environment variable.
    """
    base = "Value of environment variable {var} is undefined."
    code = 53


class InvalidImageRegistryError(RigelError):
    """
    Raised whenever an attempt is made to authenticate with an invalid Docker registry.

    :type registry: string
    :ivar registry: Name of invalid Docke registry.
    """
    base = "Invalid Docker registry '{registry}'."
    code = 54


class DockerPushError(RigelError):
    """
    Raised whenever an error occurs while pushing a Docker image to AWS ECR.

    :type msg: string
    :ivar msg: The error message as provided by the Docker API.
    """
    base = "An error occurred while pushing the Docker image to AWS ECR: {msg}."
    code = 55
