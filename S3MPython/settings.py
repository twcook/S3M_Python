"""
Copyright, 2009 - 2022, Timothy W. Cook

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Global settings for the S3Model Python library
# User editable settings are in S3MPython.conf
import os
import configparser

prjpath = os.getcwd()

config = configparser.ConfigParser()
try:
    config.read('S3MPython.conf')
except IOError:
    print("\n\nThe config file S3MPython.conf is not in the project root.\n\n")
    exit()

config['S3MPython']['prjpath'] = prjpath

print("Project path: ", prjpath)

with open('S3MPython.conf', 'w') as configfile:    # save
    config.write(configfile)

try:
    config.read('S3MPython.conf')
except IOError:
    print("\n\nThe config file S3MPython.conf is not in the project root.\n\n")
    exit()

VERSION = config['SYSTEM']['version']
RMVERSION = config['SYSTEM']['rmversion']
PRJROOT = config['S3MPython']['prjpath']
DM_LIB = config['S3MPython']['dmlib']
XML_CATALOG = config['S3MPython']['catalog']
XMLDIR = config['S3MPython']['xmldir']
RDFDIR = config['S3MPython']['rdfdir']

# Create directories if they do not exist
if not os.path.exists(DM_LIB):
    os.makedirs(DM_LIB)

if not os.path.exists(XMLDIR):
    os.makedirs(XMLDIR)

if not os.path.exists(RDFDIR):
    os.makedirs(RDFDIR)


catalog = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE catalog PUBLIC "-//OASIS//DTD XML Catalogs V1.1//EN" "http://www.oasis-open.org/committees/entity/release/1.1/catalog.dtd">
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">

  <!-- S3Model 3.1.0 RM Schema -->
  <uri name="https://www.s3model.com/ns/s3m/s3model_3_1_0.xsd" uri="(path to project root)/s3model/s3model_3_1_0.xsd"/>
  
  <!-- S3Model DMs -->
  <rewriteSystem systemIdStartString="https://dmgen.s3model.com/dmlib/" rewritePrefix="(path to project root)/DM_Library/"/>
</catalog>

"""
catalog = catalog.replace("(path to project root)", prjpath)

if not os.path.exists(XML_CATALOG):
    catfile = open(XML_CATALOG, 'w')
    catfile.write(catalog)    
    catfile.close()
    
# lxml uses the environment variable to find the catalog.xml file
os.environ["XML_CATALOG_FILES"] = XML_CATALOG


ACSFILE = config['S3MPython']['acsfile']

if not os.path.exists(ACSFILE):
    acsfile = open(ACSFILE, 'w')
    acsfile.write("Public\nPrivate\nSecret\nPII")    
    acsfile.close()


def get_acs(acsfile):
    ACS = []
    
    with open(acsfile, 'r') as f:
        for line in f:
            ACS.append(line.strip())

    return(ACS)

