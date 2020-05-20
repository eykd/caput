from setuptools import find_packages, setup

import versioneer

with open("README.rst", "r") as fi:
    long_description = fi.read()

setup(
    name="caput",
    author="David Eyk",
    author_email="eykd@eykd.net",
    description="Easy file metadata.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/eykd/caput",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
    ],
    package_dir={"": "src"},
    packages=find_packages("src"),
    install_requires=[
        "funcy",
        "pyyaml",
    ],
    version=versioneer.get_version(),
    python_requires='>=3.6',
)
