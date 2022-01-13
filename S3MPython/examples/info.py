# A simple example of using S3MPython to retrieve information about the library from the 
# configuration file.

def getInfo():
        
    import os
    print("Current Working Directory is: ", os.getcwd())

    from S3MPython.settings import VERSION, RMVERSION, DM_LIB, ACSFILE, get_acs, XMLDIR, RDFDIR, JSONDIR
    
    
    print("\n  S3MPython version:", VERSION)
    print("  S3M RM version:", RMVERSION)
    
    print("\nYou may change the following settings in the conf/S3MPython.conf file.")
    print("\nData Model Library location: ", DM_LIB)
    print("The XML catalog directory: ", os.environ["XML_CATALOG_FILES"])
    
    
    print("\n\nUsing Access Control System file: ", ACSFILE)
    print("\nACS Content: ")
    ACS = get_acs(ACSFILE)
    for s in ACS:
        print(s)
    
    print("\n\nXML data files will be in: ", XMLDIR)
    print("\nRDF data files will be in: ", RDFDIR)
    print("\nJSON data files will be in: ", JSONDIR)
    
    print("\n\n     That is all!\n\n")

if __name__ == "__main__":
    getInfo()
    exit()