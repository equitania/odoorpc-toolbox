import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="odoorpc-toolbox",
    version="0.0.2",
    author="Equitania Software GmbH",
    author_email="info@equitania.de",
    description="Helper Functions for OdooRPC.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.ownerp.io/pypi-projects/odoorpc-toolbox",
    packages=['odoorpc_toolbox'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points='''
    ''',
    install_requires=[
        'OdooRPC>=0.8.0',
        'PyYaml>=3.12'
    ]
)
