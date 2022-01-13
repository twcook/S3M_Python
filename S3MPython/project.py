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
    
    print("\nVirtual Environment: ", env_dir,"\n")
    
    # copy the configuration file and s3model files into the project.
    if not os.path.exists(os.path.join(prjpath, 's3model')):
        shutil.copytree(os.path.join(env_dir, 'S3MPython', 's3model'), os.path.join(prjpath, 's3model'))
    
    if not os.path.exists(os.path.join(prjpath, 'S3MPython.conf')):
        shutil.copyfile(os.path.join(env_dir, 'S3MPython','S3MPython.conf'), os.path.join(prjpath,'S3MPython.conf'))

    conf_file = os.path.join(prjpath,'S3MPython.conf')
    print("\nSetting project path ("+prjpath+") in S3MPython.conf\n")
    config = configparser.ConfigParser()
    config.read(conf_file)
    config.set("S3MPython", "prjpath", prjpath)

    # Write the new configuration settings.
    with open(conf_file, 'w') as configfile:
        config.write(configfile)

    print("\n\n  S3MPython initialization is complete.\n\n")

    print("Now you should configure S3MPython with project.configure()\n\n")

def configure():
    """
    Configure the S3MPython project.
    """
    conf_file = os.path.join(os.getcwd(), 'S3MPython.conf')
    config = configparser.ConfigParser()
    config.read(conf_file)

    PRJROOT = config['S3MPython']['prjpath']
    DM_LIB = config['S3MPython']['dmlib']

    if DM_LIB.lower() == 'default':
        DM_LIB = os.path.join(PRJROOT, "DM_Library")

    if not os.path.exists(DM_LIB):
        os.makedirs(DM_LIB)

    config.set('S3MPython', 'dmlib', DM_LIB)
    print("\nConfigured the Data Model Library location: ", DM_LIB)


    catalogname = config['S3MPython']['catalog']
    if catalogname.lower() == 'default':
        catalogname = PRJROOT 
    else:
        if not os.path.exists(catalogname):
            print("\n\nERROR: ", catalogname, " does not exist.")
            exit()

    if not os.path.exists(catalogname):
        os.makedirs(catalogname)
            
    if not os.path.exists(os.path.join(catalogname,'catalog.xml')):
        with open(os.path.join(catalogname,'catalog.xml'), 'w') as f:
            f.write("<?xml version='1.0' encoding='UTF-8'?>\n")
            f.write("<!DOCTYPE catalog PUBLIC '-//OASIS//DTD XML Catalogs V1.1//EN' 'http://www.oasis-open.org/committees/entity/release/1.1/catalog.dtd'>\n")
            f.write("<catalog xmlns='urn:oasis:names:tc:entity:xmlns:xml:catalog'>\n")
            f.write("  <!-- S3Model 3.1.0 RM Schema -->\n")
            f.write("  <uri name='https://www.s3model.com/ns/s3m/s3model_3_1_0.xsd' uri='" + PRJROOT + "/s3model/s3model_3_1_0.xsd'/>\n")
            f.write("\n")
            f.write("  <!-- S3Model DMs -->")
            f.write("  <rewriteSystem systemIdStartString='https://www.s3model.com/dmlib/' rewritePrefix='" + DM_LIB + "'/>\n")
            f.write("</catalog>\n")
            f.write("\n")

    config.set('S3MPython', 'catalog', catalogname)
    print("\nConfigured the XML_CATALOG location: ", catalogname + os.sep + "catalog.xml")


    ACSFILE = config['S3MPython']['acsfile']
    if ACSFILE.lower() == 'default':
        ACSFILE = os.path.join(PRJROOT, 'acs.txt')
        with open(os.path.join(PRJROOT,'acs.txt'), 'w') as f:
            f.write("Public\nPrivate\nSecret\nPII")
        
        config.set('S3MPython', 'acsfile', ACSFILE)
    else:
        if not os.path.isfile(ACSFILE):
            print("\n\nERROR: ", ACSFILE, " does not exist.")
            exit()


    print("\nConfigured the Access Control System file location: ", ACSFILE)


    XMLDIR = config['S3MPython']['xmldir']
    if XMLDIR.lower() == 'default':
        XMLDIR = os.path.join(PRJROOT, 'xmldir')
        os.makedirs(XMLDIR)
        config.set('S3MPython', 'xmldir', XMLDIR)
    else:
        if not os.path.exists(XMLDIR):
            print("\n\nERROR: ", XMLDIR, " does not exist.")
            exit()


    print("\nConfigured the XML files directory: ", XMLDIR)

    RDFDIR = config['S3MPython']['rdfdir']
    if RDFDIR.lower() == 'default':
        RDFDIR = os.path.join(PRJROOT, 'rdfdir')
        os.makedirs(RDFDIR)
        config.set('S3MPython', 'rdfdir', RDFDIR)
    else:
        if not os.path.exists(RDFDIR):
            print("\n\nERROR: ", RDFDIR, " does not exist.")
            exit()

    print("\nConfigured the RDF files directory: ", RDFDIR)

    JSONDIR = config['S3MPython']['jsondir']
    if JSONDIR.lower() == 'default':
        JSONDIR = os.path.join(PRJROOT, 'jsondir')
        os.makedirs(JSONDIR)
        config.set('S3MPython', 'jsondir', JSONDIR)
    else:
        if not os.path.exists(JSONDIR):
            print("\n\nERROR: ", JSONDIR, " does not exist.")
            exit()

    print("\nConfigured the JSON files directory: ", JSONDIR)



    print("\nWriting the new configuration file: ", conf_file)

    # Write the new configuration settings.
    with open(conf_file, 'w') as configfile:
        config.write(configfile)

    print("\n\n  S3MPython configuration is complete.\n\n")
    exit()
