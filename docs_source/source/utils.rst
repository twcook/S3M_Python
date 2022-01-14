=================
Utility Functions
=================

There are a few utility functions that you may find useful.


info.py
-------

- The **getInfo** function calls the settings script in S3MPython, which is driven by *S3MPython.conf* and prints version numbers and paths to the terminal.

- Start a Python shell::

    python

- At the ">>>" python prompt enter this command::

    from S3MPython.examples import info
    info.getInfo()

*This function will be moved into utils.py in a future release.*

utils.py
--------

Many of these functions are used to generate random, valid values for examples but you may find some useful in your own applications or demos.

fetch_acs(link)::
    
    Return an access control system list from a link. It can be a local file or a URL.
    The file must be a plain text file.
    Each access control tag must be on a separate line.
    A default file is included with S3MPython if none is specified in S3MPython.conf

reg_ns()::

    Return an etree object with registered namespaces.
    
get_latlon()::

    Return a random pair of [latitude, longitude] values.
        
random_dtstr(start=None, end=None)::

    Return a random datetime string between start and end.
    
valid_cardinality(self, v)::
    
    A dictionary of valid cardinality values and the lower and upper values of the minimum and maximum
    occurrences allowed.

    The requested setting is then tested for a valid setting.
    Example:

                 minOccurs      maxOccurs
    'setting':((lower,upper),(lower,upper))

    A Python value of 'None' equates to 'unbounded' or 'unlimited'.    

xsdstub(model)::
    
    Write the model to a XML Schema file wrapped with a root element and
    namespace declarations.

xmlstub(model, example=False)::
    
    Write the model data to a XML file wrapped with a root element and
    namespace declarations.

jsonstub(model, example=False)::
    
    Write the model data to a JSON file.    

