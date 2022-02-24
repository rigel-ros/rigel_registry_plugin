from rigelcore.exceptions import RigelError


class InvalidAWSCredentialsError(RigelError):
    """
    Raised whenever an attempt is made to authenticate with AWS ECR using invalid access credentials.
    """
    base = "Invalid AWS access credentials. Unable to authenticate with AWS ECR."
    code = 50
