import setuptools
from glob import glob


with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = [
    "aioredis==1.3.1",
    "aiohttp==3.8.1",
    "deepdiff==4.0.9",
    "gitpython==3.1.30",
    "jsonschema==3.2.0",
    "miracle-acl==0.0.4.post1",
    "pyjwt==1.7.1",
    "python-box==4.0.4",
    "redis==3.3.11",
    "yarl>=1.7.2",
    "pyros-genmsg==0.5.8",
    "rospkg==1.4.0",
    "py3rosmsgs==1.18.2",
    "cachetools==5.3.1",
    "movai-core-shared==3.0.0.*"
]


data_files = [file for file in glob("dal/validation/schema/1.0/*.json")]
data_files += [file for file in glob("dal/validation/schema/2.0/*.json")]
data_files += [file for file in glob("dal/validation/schema/2.4/*.json")]
data_files += [file for file in glob("dal/validation/schema/2.4/common/*.json")]

# TODO Adapt your project configuration to your own project.
# The name of the package is the one to be used in runtime.
# The 'install_requires' is where you specify the package dependencies of your package. They will be automaticly installed, before your package.  # noqa: E501
setuptools.setup(
    name="data-access-layer",
    version="3.0.1-1",
    author="Backend team",
    author_email="backend@mov.ai",
    description="DATA ACCESS LAYER",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MOV-AI/data-access-layer",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=["Programming Language :: Python :: 3"],
    install_requires=requirements,
    data_files=data_files,
    entry_points={
         "console_scripts":[
             "dal_backup = dal.tools.backup:main",
             "edit_yaml = dal.tools.edit_yaml:main",
             "secret_key = dal.tools.secret_key:main"
         ]
        },
)
