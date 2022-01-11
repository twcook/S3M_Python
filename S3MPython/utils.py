"""
Utility functions to support data generation etc.

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
from random import randint, choice, uniform, randrange
from datetime import datetime, date, time, timedelta
from decimal import Decimal

def fetch_acs(link):
    """
    Return an access control system list from a link. It can be a local file or a URL.
    The file must be a plain text file.
    Each access control tag must be on a separate line.
    A default file is included with S3MPython if none is specified in S3MPython.conf
    """
    # TODO: Implement URL retrieval

    acslist = []
    try:
        with open(link, 'r') as f:
            for line in f:
                acslist.append(line)
    except:
        raise IOError("Could not get the access control list from " + str(link))

    return(acslist)


def reg_ns():
    """
    Return an etree object with registered namespaces.
    """
    #  TODO: Implement customizable list to add to the defaults.
    
    ns_dict = {}
    ns_dict['vc']="http://www.w3.org/2007/XMLSchema-versioning"
    ns_dict['xsi']="http://www.w3.org/2001/XMLSchema-instance"
    ns_dict['rdfs']="http://www.w3.org/2000/01/rdf-schema#"
    ns_dict['rdf']="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    ns_dict['owl']="http://www.w3.org/2002/07/owl#"
    ns_dict['xs']="http://www.w3.org/2001/XMLSchema"
    ns_dict['xsd']="http://www.w3.org/2001/XMLSchema#"
    ns_dict['dc']="http://purl.org/dc/elements/1.1/"
    ns_dict['dct']="http://purl.org/dc/terms/"
    ns_dict['skos']="http://www.w3.org/2004/02/skos/core#"
    ns_dict['foaf']="http://xmlns.com/foaf/0.1/"
    ns_dict['schema']="http://schema.org/"
    ns_dict['sioc']="http://rdfs.org/sioc/ns#"
    ns_dict['sh']="http://www.w3.org/ns/shacl#"
    ns_dict['s3m']="https://www.s3model.com/ns/s3m/"

    return(ns_dict)

def get_latlon():
    """
    Return a random pair of [latitude, longitude] values.
    """
    latlon = [0, 0]
    latlon[0] = str(float(Decimal(randrange(-90, 90))))
    latlon[1] = str(float(Decimal(randrange(-180, 180))))
    return(latlon)


def random_dtstr(start=None, end=None):
    """
    Return a random datetime string between start and end.
    """
    if not start:
        start = datetime.strptime('1970-01-01', '%Y-%m-%d')
    else:
        start = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S')

    if not end:
        end = datetime.strptime('2015-12-31', '%Y-%m-%d')
    rand_dts = datetime.strftime(
        start + timedelta(seconds=randint(0, int((end - start).total_seconds()))), '%Y-%m-%dT%H:%M:%S')
    return rand_dts


def valid_cardinality(self, v):
    """
    A dictionary of valid cardinality values and the lower and upper values of the minimum and maximum
    occurrences allowed.

    The requested setting is then tested for a valid setting.
    Example:

                 minOccurs      maxOccurs
    'setting':((lower,upper),(lower,upper))

    A Python value of 'None' equates to 'unbounded' or 'unlimited'.
    """
    c = {'act': ((0, 1), (0, 1)), 'ev': ((0, 1), (0, 1)), 'vtb': ((0, 1), (0, 1)), 'vte': ((0, 1), (0, 1)), 'tr': ((0, 1), (0, 1)),
         'modified': ((0, 1), (0, 1)), 'location': ((0, 1), (0, 1)), 'relation_uri': ((0, 1), (0, 1)), 'value': ((0, 1), (0, 1)),
         'units': ((0, 1), (0, 1)), 'size': ((0, 1), (0, 1)), 'encoding': ((0, 1), (0, 1)), 'language': ((0, 1), (0, 1)),
         'formalism': ((0, 1), (0, 1)), 'media_type': ((0, 1), (0, 1)), 'compression_type': ((0, 1), (0, 1)), 'link': ((0, 1), (0, 1)),
         'hash_result': ((0, 1), (0, 1)), 'hash_function': ((0, 1), (0, 1)), 'alt_txt': ((0, 1), (0, 1)), 'referencerange': ((0, 1), (0, Decimal('Infinity'))),
         'normal_status': ((0, 1), (0, 1)), 'magnitude_status': ((0, 1), (0, 1)), 'error': ((0, 1), (0, 1)), 'accuracy': ((0, 1), (0, 1)),
         'numerator': ((0, 1), (0, 1)), 'denominator': ((0, 1), (0, 1)), 'numerator_units': ((0, 1), (0, 1)),
         'denominator_units': ((0, 1), (0, 1)), 'ratio_units': ((0, 1), (0, 1)), 'date': ((0, 1), (0, 1)), 'time': ((0, 1), (0, 1)),
         'datetime': ((0, 1), (0, 1)), 'day': ((0, 1), (0, 1)), 'month': ((0, 1), (0, 1)), 'year': ((0, 1), (0, 1)), 'year_month': ((0, 1), (0, 1)),
         'month_day': ((0, 1), (0, 1)), 'duration': ((0, 1), (0, 1)), 'view': ((0, 1), (0, 1)), 'proof': ((0, 1), (0, 1)),
         'reason': ((0, 1), (0, 1)), 'committer': ((0, 1), (0, 1)), 'committed': ((0, 1), (0, 1)), 'system_user': ((0, 1), (0, 1)),
         'location': ((0, 1), (0, 1)), 'performer': ((0, 1), (0, 1)), 'function': ((0, 1), (0, 1)), 'mode': ((0, 1), (0, 1)),
         'start': ((0, 1), (0, 1)), 'end': ((0, 1), (0, 1)), 'party_name': ((0, 1), (0, 1)), 'party_ref': ((0, 1), (0, 1)),
         'party_details': ((0, 1), (0, 1))}

    key = c.get(v[0])

    if key is None:
        raise ValueError("The requested setting; " + str(v[0]) + " is not a valid cardinality setting value.")
    else:
        if v[1][0] < c[v[0]][0][0] or v[1][0] > c[v[0]][0][1]:
            raise ValueError("The minimum occurences value for " + str(v) + "is out of range. The allowed values are " + str(c[v[0]][0]))
        if v[1][1] < c[v[0]][1][0] or v[1][1] > c[v[0]][1][1]:
            raise ValueError("The maximum occurences value for " + str(v) + "is out of range. The allowed values are " + str(c[v[0]][1]))
        return(True)

def xsdstub(model):
    """
    Write the model to a XML Schema file wrapped with a root element and
    namespace declarations.
    """
    print('Writing model for ', model, ' to stub.xsd')
    with open('stub.xsd', 'w') as f:
        f.write("""<?xml version='1.0' encoding='UTF-8'?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
      xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
      xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
      xmlns:vc="http://www.w3.org/2007/XMLSchema-versioning" xmlns:s3m="https://www.s3model.com/ns/s3m/"
      targetNamespace="https://www.s3model.com/ns/s3m/">
      <xs:include schemaLocation="https://www.s3model.com/ns/s3m/s3model_3_1_0.xsd"/>

    <xs:element name="root"/> <!-- This is a wrapper for the stub instance. It is not part of S3Model. -->

    """)

        f.write(model.getModel())
        f.write("</xs:schema>\n")

def xmlstub(model, example=False):
    """
    Write the model data to a XML file wrapped with a root element and
    namespace declarations.
    """
    print('Writing data instance for ', model, ' to stub.xml')
    with open('stub.xml', 'w') as f:
        f.write("""<?xml version='1.0' encoding='UTF-8'?>
    <s3m:root xmlns:xs="http://www.w3.org/2001/XMLSchema"
      xmlns:s3m="https://www.s3model.com/ns/s3m/"
      targetNamespace="https://www.s3model.com/ns/s3m/"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation='https://www.s3model.com/ns/s3m/ stub.xsd'
    >

    """)

        f.write(model.getXMLInstance(example))
        f.write("</s3m:root>\n")

def jsonstub(model, example=False):
    """
    Write the model data to a JSON file.
    """
    print('Writing JSON data instance for ', model, ' to stub.json')
    with open('stub.json', 'w') as f:
        f.write(model.getJSONInstance(example))
