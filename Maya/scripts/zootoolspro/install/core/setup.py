from setuptools import setup, find_namespace_packages
import os
import json

source_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(source_path, "package.json"), "r") as f:
    _zoo_package = json.load(f)

setup(
    name=_zoo_package["name"],
    version=_zoo_package["version"],
    description=_zoo_package["description"],
    license="LICENSE",
    author=_zoo_package["author"],
    author_email=_zoo_package["authorEmail"],
    url="git@gitlab.com:zootoolspro/zoo_tools.git",
    scripts=["scripts/zoo_cmd.py"],
    packages=find_namespace_packages(),
    zip_safe=False,
    install_requires=["GitPython"],
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development",
        "Topic :: System :: Software Distribution"
    ]
)
