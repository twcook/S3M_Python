.. _init:

===================
Project Integration
===================

After installing S3MPython into your project, it must be initialized and configured.

Initialization
==============

After :ref:`installing <install>` S3MPython into your project virtual environment.

Initialization is required to place necessary files into your project.

Follow these steps in a terminal in your **project root directory**.

.. code-block:: sh

    python3

You will now be inside a Python3 interpreter configured as your virtual environment.

.. _note:
     
     Your terminal will now show the Python interpreter prompt which is **>>>**

Execute each of the lines below, in sequence.

.. code-block:: py3

    from S3MPython import project
    project.init()


After this is complete you should perform the additional configuration steps below.

Configuration
=============

S3MPython has a significant number of configuration options, all with reasonable defaults.

When the project is initialized a copy of the file *S3MPython.conf* is placed in the directory of your project root as well as a directory named *s3model*. This directory contains the validation files and ontology for S3Model.

Below is a copy of the *S3MPython.conf*. Using your favorite **plain-text editor**, you should open the *S3MPython.conf* file in your project, it will not have comments. Also the **prjpath:** variable should have the complete path to your project root as its value.

.. code-block:: ini

    ; S3MPython.conf is the configuration
    [S3MPython]
    ; the project path is written during project init.
    prjpath:

    ; enter the full path to where you want to store the exported data models
    ; default will create a directory in the project root directory called 'DM_Library'
    dmlib: default

    ; enter the full path to where you want to store the XML catalog file
    ; default will create a directory in the project directory called 'catalog.xml'
    catalog: default

    ; enter the full path to an Access Control System file.
    ; default will create a simple default file in the project directory 'acs.txt'
    acsfile: default

    ; enter the full path to where you want to store the generated XML
    ; enter None if you configured a repository below. The default is 'xmldir' in the project directory.
    xmldir: default

    ; enter the full path to where you want to store the generated RDF
    ; enter None if you configured a repository below. The default is 'rdfdir' in the project directory.
    rdfdir: default
   
    ; enter the full path to where you want to store the generated JSON
    ; enter None if you configured a repository below. The default is 'jsondir' in the project directory.
    jsondir: default

    [NAMESPACES]
    ; any additional namespaces must be defined here with their abbreviations. One per line.
    ; abbrev = namespace URI 

    foaf: http://xmlns.com/foaf/0.1/

    ; Below are where repository setups are defined for each of the three types of data generation.
    ; If a type is to be generated but no repository is defined for the type. Then the data will be generated
    ; and written to the filesystem in a subdirectory of the output directory.


    ; A default repository where we can write the output XML instead of to the filesystem.
    ; The config will only process the first one with an ACTIVE status.

    [BASEX]
    status: INACTIVE
    host: localhost
    port: 1984
    dbname: S3MPython
    user: admin
    password: admin

    ; A default repository where we can write the output RDF instead of to the filesystem.
    ; The config will only process the first one with an ACTIVE status.

    [ALLEGROGRAPH]
    status: INACTIVE
    host: localhost
    port: 10035
    repo: S3MPython
    user: admin
    password: admin


    ; MarkLogic is a multi-model database, select the types of data to load by entering 'True' as the load*** value
    ; the port number will be used to attach your REST API
    ; the forests key is the number of forests to create, 1 to 99
    ; the user MUST have the manage-admin role/priviliges
    [MARKLOGIC]
    status: INACTIVE
    loadxml: True
    loadrdf: True
    loadjson: True
    hostip: 192.168.25.120
    hostname: localhost.localdomain
    port: 8020
    dbname: S3MPython
    forests: 2
    user: admin
    password: admin


    ; There are no user editable options in the SYSTEM section.

    [SYSTEM]
    version: 3.1.0.20
    rmversion: 3.1.0


In the **[SYSTEM]** section at the bottom, do not edit anything. These version numbers are important for proper operation of S3MPython. 

In the **[S3MPython]** section:
*These are all optional to edit. A resonable default will be used if you leave them set to default.*

    - be sure that the project path is correct

    - for the **dmlib** value enter an existing pathname if you do not want the system to use the default
    
    - for the **catalog** value enter an existing pathname if you do not want the system to use the default
    
    - for the **acsfile** value enter an existing pathname and filename if you do not want the system to use the default
    
    - for the **xmldir**, **jsondir** and **rdfdir** values enter an existing pathname if you do not want the system to use the default. The *defaults* for these are subdirectories of your project. 
    
If you are using one of the repositories below it will override the filesystem storage option.

In the **[NAMESPACES]** section:

    - Enter any project specific namespaces that you are using. There is one example namespace added. Use the format shown, one per line. The abbreviation *foaf* stands for `Friend of a Friend <http://xmlns.com/foaf/spec/>`_ is an example that will be used. If you aren't using this one then delete the line.  See the `Solution <https://s3model.com/userguide/docs/S3Model.html#the-solution>`_ section in the User Guide for more information.


In the **[BASEX]**, **[ALLEGROGRAPH]**, **[MARKLOGIC]**, sections:

    - complete any required information in order to use the respective repository.
    - be sure to change the **status** to *ACTIVE* for the one you want to use.

After you are satisfied with the configuration options follow these steps in a terminal in your **project root directory**.

.. code-block:: py3

    project.configure()


**IF** you happened to have exited the Python interpreter in your terminal. You will need to restart it and run the configure function::

    |    >>>python3

    You will now be inside a Python3 interpreter configured as your virtual environment.
    *NOTE:* Your terminal will now show the Python interpreter prompt which is **>>>**

    Execute each of the lines below, in sequence.

    |    >>>from S3MPython import project
    |    >>>project.configure()


This completes your S3MPython configuration.

You can use the library to create S3Model models.

For hands on experience we recommend that you start with the `S3MPython Training Examples <https://github.com/twcook/S3M_Python_Training_examples>`_. This is a set of Jupyter notebooks that walk through each of the data model components. The instructions for this tutorial is in the `User Guide <https://s3model.com/userguide/docs/index.html>`_.

Then move on to the tutorials in this guide.
