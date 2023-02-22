Project Integration
===================

After installing S3MPython into your project, it must be initialized and configured.

Initialization
--------------

Initialization is required to place required files into your project.

Follow these steps in a terminal in your **project root directory**.

.. code-block:: sh

    python3

You will now be inside a Python3 interpreter configured as your virtual environment (S3MPy).
*NOTE:* Your terminal will now show the Python interpreter prompt which is **>>>**

Execute each of the lines below, in sequence.

.. code-block:: py3

    from S3MPython import project
    project.init()


After this is complete you should perform the additional configuration steps below.

Configuration
-------------

S3MPython has a significant number of configuration options, all with reasonable defaults.

When the project is initialized a copy of *S3MPython.conf* is placed in the *conf* subdirectory of your project root.

This is a copy of the *S3MPython.conf* file with comments. If you open the *conf/S3MPython.conf* file in your project, it will not have comments. Also the **prjpath:** variable should have the complete path to your project root as its value.



.. code-block:: ini

    ; S3MPython.conf is the configuration
    [S3MPython]
    ; the project path is written during project init.
    prjpath:

    ; enter the full path to where you want to store the exported data models
    ; default will create a directory in the project root directory called 'dmlib'
    dmlib: default

    ; enter the full path to where you want to store the XML catalog file
    ; default will create a directory in the users home directory called 'S3MPython/catalogs/catalog.xml'
    catalog: default

    ; enter the full path to an Access Control System file.
    ; default will create a simple default file in the users home directory 'S3MPython/acs.txt'
    acsfile: default

    ; enter the full path to where you want to store the generated XML
    ; enter None if you configured a repository below.
    xmldir: xmldir

    ; enter the full path to where you want to store the generated RDF
    ; enter None if you configured a repository below.
    rdfdir: rdfdir

    [NAMESPACES]
    ; any additional namespaces must be defined here with their abbreviations.
    ; {abbrev}:{namespace URI}

    dul: http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#


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


    ; MarkLogic is a multi-model DB, select the types of data to load by entering 'True' as the load*** value
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
    version: 3.1.0.12
    rmversion: 3.1.0


In the **[SYSTEM]** section at the bottom, do not edit anything.

In the **[S3MPython]** section:

    - be sure that the project path is correct
    - for the **dmlib** value enter an existing pathname if you do not want the system to use the default
    - for the **catalog** value enter an existing pathname if you do not want the system to use the default
    - for the **acsfile** value enter an existing pathname and filename if you do not want the system to use the default
    - for the **xmldir** and **rdfdir** values enter an existing pathname if you do not want the system to use the default or enter *None* if you are using one of the repositories that we support.


In the **[NAMESPACES]** section:

    - Enter any project specific namespaces that you are using.



In the **[BASEX]**, **[ALLEGROGRAPH]**, **[MARKLOGIC]**, sections:

    - complete any required information in order to use the respective repository.
    - be sure to change the **status** to *ACTIVE* for the one(s) you want to use.


After you are satisfied with the configuration options follow these steps in a terminal in your **project root directory**.

.. code-block:: sh

    python3

You will now be inside a Python3 interpreter configured as your virtual environment (S3MPy).
*NOTE:* Your terminal will now show the Python interpreter prompt which is **>>>**

Execute each of the lines below, in sequence.

.. code-block:: py3

    from S3MPython import project
    project.configure()

This completes your S3MPython configuration.

You can use the library to create S3Model models.

For hands on experience we recomend that you start with the `S3MPython Examples <http://s3model.com/S3MPython_examples/>`_.

