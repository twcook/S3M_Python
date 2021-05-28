# S3MPython

[![Build Status](https://travis-ci.com/DataInsightsInc/S3MPython.svg?branch=master)](https://travis-ci.com/s3model/S3MPython)


A Python library for creating S3Model data models.


# Examples & Training

For S3Model training courses see the [S3Model](https://s3model.com) website.

There is a repository called S3MPython_examples meant to be your first experience with S3MPython.

# Installation

Install into your project environment with:

```
  pip install <path/to/release/file>
```

The <path/to/release/file> is found by going to the [Releases page](https://github.com/s3model/S3MPython/releases) under the Release you want (usually the latest) go to the Source code link, right click on it and copy the link location.

See the **Project Integration** section of the [documentation](https://s3model.com/S3MPython/) for the next steps.


# Development

Clone the master [repository](https://github.com/s3model/S3MPython/tree/master)

```
git clone git@github.com:s3model/S3MPython.git
```

Change to the new directory and using conda, build the environment.

```
cd S3MPython

conda env create -f S3MPython.yml
```

Create a new branch for your changes.


Build and install your development branch into your S3MPython environment.

```
python3 setup.py sdist bdist_wheel

pip install e .
```
