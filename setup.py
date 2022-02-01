import setuptools

with open('./README.md', 'r') as readme:
    long_description = readme.read()

setuptools.setup(
    name='ecr_rigel_plugin',
    version='0.0.1',
    author='Pedro Melo',
    author_email='pedro.m.melo@inesctec.pt',
    description='A plugin for Rigel to ease the deployment of Docker images to AWS ECR.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.8',
    install_requires=[
        'boto3==1.20.44',
        'docker==4.1.0'
    ],
    py_modules=['ecr_rigel_plugin']
)
