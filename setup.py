import os

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    LONG_DESCRIPTION = "\n" + f.read()

VERSION = "0.1.0"
DESCRIPTION = "Solve leetcode questions without the need of a browser."

# Setting up
setup(
    name="local-leetcode",
    version=VERSION,
    author="Jakob Roithinger",
    author_email="jakob.roithinger@icloud.com",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=["bs4", "requests"],
    keywords=["leetcode"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
)
