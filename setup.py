import os

import setuptools
from os import listdir

with open("README.md", "r") as fh:
    long_description = fh.read()

data_files = ["dal/validation/schema/1.0/" + file for file in os.listdir("dal/validation/schema/1.0")]
data_files += ["dal/validation/schema/2.0/" + file for file in os.listdir("dal/validation/schema/2.0")]

# TODO Adapt your project configuration to your own project.
# The name of the package is the one to be used in runtime.
# The 'install_requires' is where you specify the package dependencies of your package. They will be automaticly installed, before your package.  # noqa: E501
setuptools.setup(
    name="dal",
    version="1.0.0-19",
    author="Backend team",
    author_email="backend@mov.ai",
    description="Dummy description",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MOV-AI/data-access-layer",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=["Programming Language :: Python :: 3"],
    install_requires=["jsonschema==3.2.0", "gitpython==3.1.2",
                      "py3rosmsgs", "aioredis==1.3.0", "redis==3.3.11", "Pillow>=5.1.0",
                      "pyros-genmsg", "python-box==4.0.4", "deepdiff==4.0.9",
                      "miracle-acl==0.0.4.post1", "pyjwt==1.7.1"],
    data_files=data_files,
    entry_points={},
)
