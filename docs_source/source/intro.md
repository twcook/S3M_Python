# Introduction and Installation

## Purpose

**S3MPython** is a Python implementation of the [S3Model](https://s3model.com) specifications.

### Target Audience

This library provides the ability for [domain experts](https://s3model.com/specifications/docs/glossary.html#domain-expert) from any field, with some programming
ability to build S3Model data models.

Programmers, data engineers and data scientists can also benefit from this library in the same ways as
domain experts as long as they understand the [domain ontologies and vocabularies](https://s3model.com/specifications/docs/glossary.html#ontology) to use for the semantic markup.

**For hands on experience** we recommend that you start with the [S3MPython Training Examples](https://github.com/twcook/S3M_Python_Training_examples). The **tutorial** for these examples is located in the [S3Model User Guide](https://s3model.com/userguide/docs/index.html) It is *highly* recommended that those new to S3Model read the User Guide in it's entirety before doing the tutorial.

(install)=

## Installation

You should install S3MPython into the [virtual environment](https://docs.python.org/3/tutorial/venv.html) where you are developing your application.

```sh
pip install S3MPython
```

The latest *release candidate* can be installed from the [Github](https://github.com/twcook/S3M_Python/) project.

```sh
pip install  <path/to/release/file>
```

The *\<path/to/release/file>* is found by going to the [Releases page](https://github.com/twcook/S3M_Python/releases) under the Release you want (usually the latest) go to the Source code link, right click on it and copy the link location.

See the **Project Integration** section of the [documentation](https://s3model.com/S3MPython/docs/config.html) for the next steps.

## Development

### Cross-Platform on Anaconda

Anaconda is the **preferred environment** for a tool like S3MPython because it integrates easily with systems for domain experts, data engineers, and data scientists.

- [Download and install](https://www.continuum.io/downloads) the latest Anaconda Python for your platform.
- More detailed Anaconda instructions are [here](https://docs.continuum.io/anaconda/install/)  if you prefer.
- Open a terminal window and create a conda environment. On Windows it is best to open an *Anaconda Prompt* terminal from the Anaconda menu:
- Create and change to the directory

```sh
mkdir S3MPythonTest
```

```sh
cd S3MPythonTest
```

- Create the environment

```sh
conda env create -f S3MPython.yml
```

```sh
source activate S3MPython
```

```sh
pip install S3MPython
```

Create a new branch for your changes.

Build and install your development branch into your S3MPython environment.

```sh
python setup.py sdist bdist_wheel

pip install e .
```

These quick steps create a virtual environment in the subdirectory *S3MPython*.
Once the environment is created, conda displays how to activate the environment.
When activated, S3MPython is installed in the subdirectory along with the environment.

## What are all the files for?

Depending on how and where you installed S3MPython you will see a varying number of files and
subdirectories. Many of them may be part of the Anaconda environment, so we do not cover those.

Referenced from the *S3MPython* directory created at install time:

### Files

- README.md
  : A brief explanation of the library's purpose and links to background information.
- S3MPython.conf
  : This file is the required configuration file.
- LICENSE
  : A copy of the *copyright notice* and *usage license*.

### Directories

- docs
  : S3MPython HTML documentation. Open the index.html file in a browser.
- s3model
  : Support files required for operation.

    - s3model.owl - the core S3Model ontology.
    - s3model_4_0_0.xsd - the reference model schema version 4.4.0
    - s3model_4_0_0.rdf - the extracted semantics from the reference model schema version 3.1.0
    - s3model_4_0_0.xsl - a stylesheet providing visualization in a browser of the reference model schema version 3.1.0
    - dm-description.xsl - a stylesheet that provides for visualization in a browser of any S3Model data model. Just place it in the same directory with the dm-\{cuid}.xsd file and open the schema in a browser.
- S3MPython
  : The library source code.
