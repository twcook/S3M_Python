=========
Tutorials
=========

See the S3Model Introduction Tutorial in the `User Guide <https://s3model.com/userguide/docs/index.html>`_ page.

Examples
========

- Create a directory for testing the *Examples*::

    mkdir S3MPythonExamples

- Change to the directory::

    cd S3MPythonExamples

- Create a virtual environment. Here we are using `Anaconda <https://www.anaconda.com/products/individual>`_.::

    conda create -n S3MPythonExamples S3MPython

- Activate the environment::

    conda activate S3MPythonExamples


- Install S3MPython::

    pip install S3MPython


- Now you must follow the instructions for **Project Integration**. 

See the :ref:`Initialization and Configuration documentation <init>` for the next steps.



- In your virtual environment there is a file name *S3MPython.conf* and a folder named *s3model*. If you followed the above instructions they are in; *~/anaconda3/envs/S3MPythonExamples/S3MPython*. Copy them to your project directory. In this example it is *S3MPythonExamples*.

See the
info.py
-------

- The **getInfo** function calls the settings script in S3MPython, which is driven by *S3MPython.conf* and prints version numbers and paths to the terminal.

- Start a Python shell::

    python

- At the ">>>" python prompt enter this command::

    from S3MPython.examples import info


- **DataModel01.py** creates a full data model like the one from the Introduction tutorial.

- **DataModel02.py** creates a data model example for an `IoT device <https://internetofthingsagenda.techtarget.com/definition/IoT-device>`_. Specifically a ??????


Remove Example Environment
--------------------------

Use these commands::

    conda deactivate
    conda remove --name S3MPythonExamples --all
