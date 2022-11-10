import setuptools
from glob import glob


with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = []

with open("requirements.txt", "r") as fh:
    for line in fh.readlines(): 
        if line != '\n':
            if '\n' in line:
                line = line.rstrip('\n')
            requirements.append(str(line))


data_files = [file for file in glob("dal/validation/schema/1.0/*.json")]
data_files += [file for file in glob("dal/validation/schema/2.0/*.json")]
data_files += [file for file in glob("dal/validation/schema/2.3/*.json")]
data_files += [file for file in glob("dal/validation/schema/2.3/common/*.json")]

# TODO Adapt your project configuration to your own project.
# The name of the package is the one to be used in runtime.
# The 'install_requires' is where you specify the package dependencies of your package. They will be automaticly installed, before your package.  # noqa: E501
setuptools.setup(
    name="dal",
    version="1.0.1-0",
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
             "backup = dal.tools.backup:main",
             "edit_yaml = dal.tools.edit_yaml:main",
             "secret_key = dal.tools.secret_key:main"
         ]
        },
)
