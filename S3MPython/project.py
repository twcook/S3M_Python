import shutil
import os
import sys
import configparser


def init(prjpath=None):

    """
    Initialize a S3MPython project in prjpath.
    """


    # if there is no prjpath then assign the project home directory
    if not prjpath:
        prjpath = os.getcwd()


    env_dir = sys.prefix  # get the location of the default files after installation of S3MPython
    shutil.copytree(os.path.join(env_dir, 'S3MPython', 's3model'), os.path.join(prjpath, 's3model'))
    shutil.copytree(os.path.join(env_dir, 'S3MPython', 'conf'), os.path.join(prjpath, 'conf'))

    conf_file = os.path.join(prjpath, 'conf', 'S3MPython.conf')
    print("Setting project path in conf/S3MPython.conf")
    config = configparser.ConfigParser()
    config.read(conf_file)
    config.set("S3MPython", "prjpath", prjpath)

    # Write the new configuration settings.
    with open(conf_file, 'w') as configfile:
        config.write(configfile)

    print("\n\n  S3MPython initialization is complete.\n\n")

    exit()

def configure():
    """
    Configure the S3MPython project.
    """
    conf_file = os.path.join(os.getcwd(), 'conf', 'S3MPython.conf')
    config = configparser.ConfigParser()
    config.read(conf_file)

    PRJROOT = config['S3MPython']['prjpath']
    DM_LIB = config['S3MPython']['dmlib']

    if DM_LIB.lower() == 'default':
        DM_LIB = os.path.join(PRJROOT, "dmlib")

    if not os.path.exists(DM_LIB):
        os.makedirs(DM_LIB)

    config.set('S3MPython', 'dmlib', DM_LIB)
    print("\nConfigured the Data Model Library location: ", DM_LIB)


    catdir = config['S3MPython']['catalog']
    if catdir.lower() == 'default':
        catdir = os.path.join(PRJROOT, 'catalogs')
    else:
        if not os.path.exists(catdir):
            print("\n\nERROR: ", catdir, " does not exist.")
            exit()

    if not os.path.exists(catdir):
        os.makedirs(catdir)
        with open(catdir + os.sep + 'catalog.xml', 'w') as f:
            f.write("<?xml version='1.0' encoding='UTF-8'?>\n")
            f.write("<!DOCTYPE catalog PUBLIC '-//OASIS//DTD XML Catalogs V1.1//EN' 'http://www.oasis-open.org/committees/entity/release/1.1/catalog.dtd'>\n")
            f.write("<catalog xmlns='urn:oasis:names:tc:entity:xmlns:xml:catalog'>\n")
            f.write("  <!-- S3Model 3.1.0 RM Schema -->")
            f.write("  <uri name='https://www.s3model.com/ns/s3m/s3model_3_1_0.xsd' uri='s3model_3_1_0.xsd'/>\n")
            f.write("\n")
            f.write("  <!-- S3Model DMs -->")
            f.write("  <rewriteSystem systemIdStartString='https://www.s3model.com/dmlib/' rewritePrefix='" + DM_LIB + "'/>\n")
            f.write("</catalog>\n")
            f.write("\n")

    config.set('S3MPython', 'catalog', catdir)
    print("\nConfigured the XML_CATALOG location: ", catdir)


    ACSFILE = config['S3MPython']['acsfile']
    if ACSFILE.lower() == 'default':
        ACSFILE = os.path.join(PRJROOT, 'conf', 'acs.txt')
        config.set('S3MPython', 'acsfile', ACSFILE)
    else:
        if not os.path.isfile(ACSFILE):
            print("\n\nERROR: ", ACSFILE, " does not exist.")
            exit()


    print("\nConfigured the Access Control System file location: ", ACSFILE)


    XMLDIR = config['S3MPython']['xmldir']
    if XMLDIR.lower() == 'xmldir':
        XMLDIR = os.path.join(PRJROOT, 'xmldir')
        os.makedirs(XMLDIR)
        config.set('S3MPython', 'xmldir', XMLDIR)
    else:
        if not os.path.exists(XMLDIR):
            print("\n\nERROR: ", XMLDIR, " does not exist.")
            exit()


    print("\nConfigured the XML files directory: ", XMLDIR)

    RDFDIR = config['S3MPython']['rdfdir']
    if RDFDIR.lower() == 'rdfdir':
        RDFDIR = os.path.join(PRJROOT, 'rdfdir')
        os.makedirs(RDFDIR)
        config.set('S3MPython', 'rdfdir', RDFDIR)
    else:
        if not os.path.exists(catdir):
            print("\n\nERROR: ", RDFDIR, " does not exist.")
            exit()

    print("\nConfigured the RDF files directory: ", RDFDIR)



    print("\nWriting the new configuration file: ", conf_file)

    # Write the new configuration settings.
    with open(conf_file, 'w') as configfile:
        config.write(configfile)

    print("\n\n  S3MPython configuration is complete.\n\n")
    exit()
