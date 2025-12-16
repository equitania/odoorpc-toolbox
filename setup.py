import setuptools
import re

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read version from _version.py without importing the package
with open("odoorpc_toolbox/_version.py", "r", encoding="utf-8") as fh:
    version_match = re.search(r"^__version__\s*=\s*['\"]([^'\"]*)['\"]", fh.read(), re.M)
    version = version_match.group(1) if version_match else "0.0.0"

setuptools.setup(
    name="odoorpc-toolbox",
    version=version,
    author="Equitania Software GmbH",
    author_email="info@equitania.de",
    description="Helper Functions for OdooRPC.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/equitania/odoorpc-toolbox",
    packages=['odoorpc_toolbox'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    entry_points='''
    ''',
    install_requires=[
        'OdooRPC>=0.10.1',
        'PyYaml>=5.4.1'
    ]
)
