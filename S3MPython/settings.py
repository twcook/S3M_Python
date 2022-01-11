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

config = configparser.ConfigParser()
config.read('conf/S3MPython.conf')

VERSION = config['SYSTEM']['version']
RMVERSION = config['SYSTEM']['rmversion']
PRJROOT = config['S3MPython']['prjpath']
DM_LIB = config['S3MPython']['dmlib']
XML_CATALOG = config['S3MPython']['catalog']
# lxml uses the environment variable to find the catalog.xml file
os.environ["XML_CATALOG_FILES"] = XML_CATALOG


ACSFILE = config['S3MPython']['acsfile']

def get_acs(acsfile):
    ACS = []
    with open(acsfile, 'r') as f:
        for line in f:
            ACS.append(line.strip())

    return(ACS)

XMLDIR = config['S3MPython']['xmldir']
RDFDIR = config['S3MPython']['rdfdir']
