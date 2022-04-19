import os

import setuptools
from os import listdir

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = []
with open("requirements.txt", "r") as f:
    requirements = [a.split('\n')[0] for a in f.readlines()]

schema_files = ["dal/validation/schema/1.0/" + file for file in os.listdir("dal/validation/schema/1.0")]
schema_files += ["dal/validation/schema/2.0/" + file for file in os.listdir("dal/validation/schema/2.0")]

# TODO Adapt your project configuration to your own project.
# The name of the package is the one to be used in runtime.
# The 'install_requires' is where you specify the package dependencies of your package. They will be automaticly installed, before your package.  # noqa: E501
setuptools.setup(
    name="dal",
    version="1.0.0-17",
    author="Backend team",
    author_email="backend@mov.ai",
    description="Dummy description",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MOV-AI/data-access-layer",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=["Programming Language :: Python :: 3"],
    install_requires=requirements,
    data_files=schema_files,
    entry_points={},
)
