=============================
Introduction and Installation
=============================

Purpose
=======

**S3MPython** is a Python implementation of the `S3Model <https://s3model.com/S3Model/>`_ specifications.

Target Audience
---------------
This library provides the ability for *domain experts* from any field, with some programming
ability to build S3Model data models.

Programmers, data engineers and data scientists can also benefit from this library in the same ways as
domain experts as long as they understand the domain ontologies and vocabularies to use for the semantic markup.


**For hands on experience** we recomend that you start with the `S3MPython Examples <http://s3model.com/S3MPython_examples/>`_.




.. _install:

Installation
============

You should install S3MPython into the virtual environment where you are developing your application.

The latest version can be installed from PyPi:

.. code-block:: sh

    pip install  S3MPython

The *<path/to/release/file>* is found by going to the `Releases page <https://github.com/twcook/S3M_Python/releases>`_ under the Release you want (usually the latest) go to the Source code link, right click on it and copy the link location.

See the **Project Integration** section of the `documentation <http://s3model.com/S3MPython/config.html>`_ for the next steps.


Development
===========

Cross-Platform on Anaconda
--------------------------

Anaconda is the **preferred environment** for a tool like S3MPython because it integrates easily with systems for domain experts, data engineers, and data scientists.

- `Download and install <https://www.continuum.io/downloads>`_ Anaconda Python 3.7+ for your platform.
- More detailed Anaconda instructions are `here <https://docs.continuum.io/anaconda/install/>`_  if you prefer.


- Open a terminal window and create a conda environment. On Windows it is best to open an *Anaconda Prompt* terminal from the Anaconda menu:

- Create and change to the directory

.. code-block:: sh

    cd S3MPython

- Create the environment

.. code-block:: sh

    conda create -n S3MPython -f dev_requirements.txt


.. _activate: Activate


- Activate the environment according to the instructions shown by Anaconda in the terminal window.

**Windows**

.. code-block:: sh

    conda activate S3MPython

**or Linux/MacOSX**

.. code-block:: sh

    source activate <path/to/directory>

- install S3MPython

Create a new branch for your changes.


Build and install your development branch into your S3MPython environment.

.. code-block:: sh

    python3 setup.py sdist bdist_wheel

    pip install e .


These quick steps create a virtual environment in the subdirectory *S3MPython*.
Once the environment is created, conda displays how to activate the environment.
When activated then S3MPython is installed in the subdirectory along with the environment.


What are all the files for?
===========================

Depending on how and where you installed S3MPython you will see a varying number of files and
subdirectories. Many of them may be part of the Anaconda environment, so we do not cover those.

Referenced from the *S3MPython* directory created at install time:

Files
-----

- README.md
    A brief explanation of the library's purpose and links to background information.

- S3MPython.conf
    This file is the required configuration file.

- LICENSE
    A copy of the copyright notice and license.


Directories
-----------

- docs
    S3MPython HTML documentation. Open the index.html file in a browser.

- s3model
    Support files required for operation.

    - s3model.owl - the core S3Model ontology.
    - s3model_3_1_0.xsd - the reference model schema version 3.1.0
    - s3model_3_1_0.rdf - the extracted semantics from the reference model schema version 3.1.0
    - s3model_3_1_0.xsl - a stylesheet providing visualization in a browser of the reference model schema version 3.1.0
    - dm-description.xsl - a stylesheet that provides for visualization in a browser of any S3Model data model. Just place it in the same directory with the dm-{cuid}.xsd file and open the schema in a browser.

- S3MPython
    The library source code.
