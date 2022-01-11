"""
Meta information classes used by a data model (DMType)

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
import json
from datetime import datetime
from abc import ABC, abstractmethod
from xml.sax.saxutils import escape
from urllib.parse import quote
from typing import ByteString, Dict, List, Tuple, Iterable
from decimal import Decimal


import xmltodict
from cuid import cuid
from validator_collection import checkers

from .xdt import XdStringType, XdLinkType, XdFileType
from .struct import ClusterType
from .errors import ValidationError
from .utils import valid_cardinality

class MetaCommon(ABC):
    """
    Common properties and methods for the S3M model metaclasses.
    """
    
    @abstractmethod
    def __init__(self, label: str):
        """
        The semantic label (name of the model) is required.
        """

        self._published = False        
        self._mcuid = cuid()  # model cuid
        self._label = ''
        self._language = ''
        self._docs = ''
        self._pred_obj_list = []
        self._definition_url = ''
        self._cardinality = {}

        if checkers.is_string(label, 2):
            if len(label) > 1:
                self._label = label
            else:
                raise ValueError('label must be at least 2 characters in length')
        else:
            raise TypeError('"label" must be a string type. Not a ', type(label))

        
    @property
    def published(self):
        """
        When True, prevents further model changes.
        """
        return self._published

    @published.setter
    def published(self, v: bool):
        if isinstance(v, bool):
            if self._published == False:
                self._published = v
            else:
                raise ValueError("the published value cannot be changed once published.")
        else:
            raise TypeError("the published value must be a boolean.")

    @property
    def cardinality(self):
        """
        The cardinality status values for meta classes.

        The setter method can be called by each subclass to add cardinality
        values for each element.
        Some elements cardinality may not be changed such as most of the maxOccurs.

        The cardinality dictionary uses a string representation of each
        property name and a list as the value.

        The value passed into the setter is a tuple with v[0] as a string (key) and
        v[1] as a list containing an integer set representing the
        (minimum, maximum) values. The entire value list is replaced in the dictionary.

        Example
        --------

        ('committer', [1,1]) will set the committer value (AttestationType) to be required.


        NOTES
        -----
        The Python value of 'None' represents the 'unbounded' XML Schema value.
        None is converted to Decimal('Infinity') for comparisons in the setter.
        The 'unbounded' value is allowed on only a few attributes.

        """
        return self._cardinality

    @cardinality.setter
    def cardinality(self, v):
        if not self.published:
            if isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], list):
                v[1][0] = Decimal('INF') if v[1][0] is None else v[1][0]
                v[1][1] = Decimal('INF') if v[1][1] is None else v[1][1]

                if isinstance(v[1][0], (int, Decimal)) and isinstance(v[1][1], (int, Decimal)):
                    if isinstance(v[1][0], int) and isinstance(v[1][1], int) and v[1][0] > v[1][1]:
                        raise ValueError("The minimum value must be less than or equal to the maximum value.")
                    if valid_cardinality(self, v):
                        self._cardinality[v[0]] = v[1]
                else:
                    raise ValueError("The cardinality values must be integers or None.")
            else:
                raise ValueError("The cardinality value is malformed. It must be a tuple of a string and a list of two integers.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def language(self):
        """
        A language of the intellectual content of the resource.

        Recommended best practice for the values of the Language
        element is defined by RFC 1766 [RFC1766] which includes
        a two-letter Language Code (taken from the ISO 639
        standard [ISO639]), followed optionally, by a two-letter
        Country Code (taken from the ISO 3166 standard [ISO3166]).
        For example, 'en' for English, 'fr' for French, or
        'en-uk' for English used in the United Kingdom.
        """
        return self._language

    @language.setter
    def language(self, v):
        if self.published:
            if isinstance(v, str):
                self._language = v
            else:
                raise TypeError("the value must be a string.")
        else:
            raise ValueError("The model has not been published.")

    @property
    def label(self):
        """
        The semantic name of the component.
        """
        return self._label

    @property
    def mcuid(self):
        """
        The unique identifier of the component.
        """
        return self._mcuid

    @property
    def pred_obj_list(self):
        """
        A list of additional predicate object pairs to describe the component.

        Each list item is a tuple where 0 is the predicate and 1 is the object.

        Example:
        ('rdf:resource','https://www.niddk.nih.gov/health-information/health-statistics')
        The setter accepts the tuple and appends it to the list.
        If an empty list is supplied it resets the value to the empty list.
        """
        return self._pred_obj_list

    @pred_obj_list.setter
    def pred_obj_list(self, v: Iterable):
        if not self.published:
            if isinstance(v, list) and len(v) == 0:
                self._pred_obj_list = []
            elif isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], str):
                self._pred_obj_list.append(v)
            else:
                raise ValueError("the Predicate Object List value must be a tuple of two strings or an empty list.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def definition_url(self):
        """
        The primary definition URL for the model.
        Cannot be an IP address.
        """
        return self._definition_url

    @definition_url.setter
    def definition_url(self, v: str):
        if not self.published:
            if checkers.is_url(v):
                self._definition_url = v
            else:
                raise ValueError("the Definition URL value must be a valid URL.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def docs(self):
        """
        The human readable documentation string describing the purpose of
        the model.
        """
        return self._docs

    @docs.setter
    def docs(self, v: str):
        if not self.published:
            if checkers.is_string(v):
                self._docs = v
            else:
                raise ValueError("the Documentation value must be a string.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    def __str__(self):
        if not self.validate():
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + ', ID: ' + self.mcuid + " is not valid.")
        return(self.__class__.__name__ + ' : ' + self.label + ', ID: ' + self.mcuid)

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not checkers.is_url(self.definition_url):
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + " - failed validation: definition_url is invalid\n" + str(self.definition_url))
        elif len(self.label) < 2:
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + " - failed validation: label is too short or missing\n" + str(self.label))
        else:
            return(True)


class PartyType(MetaCommon):
    """
    Description of a party, including an optional external link to data for this 
    party in a demographic or other identity management system. An additional 
    details element provides for the inclusion of information related to this 
    party directly. 
    
    If the party information is to be anonymous then do not include the details element.
    """

    def __init__(self, label: str):
        """
        The semantic label (name of the model) is required.
        """
        super().__init__(label)

        self._party_name = None
        self._party_ref = None
        self._party_details = None
        self.cardinality = ('party_name', [0, 1])
        self.cardinality = ('party_ref', [0, 1])
        self.cardinality = ('party_details', [0, 1])

    @property
    def party_name(self):
        """
        Optional human-readable name (in String form)
        """
        return self._party_name

    @party_name.setter
    def party_name(self, v):
        if self.published:
            if isinstance(v, str):
                self._party_name = v.strip()
            else:
                raise ValueError("the party_name value must be a string.")
        else:
            raise ValueError("The model has not been published.")

    @property
    def party_ref(self):
        """
        Optional reference to more detailed demographic or identification 
        information for this party, in an external system.
        """
        return self._party_ref

    @party_ref.setter
    def party_ref(self, v):
        if not self.published:
            if isinstance(v, XdLinkType):
                self._party_ref = v
            else:
                raise ValueError("the party_ref value must be a XdLinkType.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def party_details(self):
        """
        Structural details about the party.
        """
        return self._party_details

    @party_details.setter
    def party_details(self, v):
        if not self.published:
            if isinstance(v, ClusterType):
                self._party_details = v
            else:
                raise ValueError("the party_details value must be a ClusterType.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    def validate(self):
        """
        Every Type must implement this method.
        """
        if not super(PartyType, self).validate():
            return(False)
        else:
            return(True)

    def getModel(self):
        """
        """
        if not self.published:
            raise ValueError("The model must first be published.")

        if not self.validate():
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + ', ID: ' + self.mcuid + " is not valid.")

        indent = 2
        padding = ('').rjust(indent)
        party_str = ''
        # Create the datatype
        party_str += '\n\n' + padding.rjust(indent) + ("<xs:complexType name='mc-" + self.mcuid + "'> \n")
        party_str += padding.rjust(indent + 2) + ("<xs:annotation>\n")
        party_str += padding.rjust(indent + 2) + ("<xs:documentation>\n")
        party_str += padding.rjust(indent + 4) + (escape(self.docs) + "\n")
        party_str += padding.rjust(indent + 2) + ("</xs:documentation>\n")
        # Write the semantic links. There must be the same number of attributes
        # and links or none will be written.
        party_str += padding.rjust(indent + 2) + ('<xs:appinfo>\n')
        party_str += padding.rjust(indent + 2) + ("<rdfs:Class rdf:about='mc-" + self.mcuid + "'>\n")
        party_str += padding.rjust(indent + 2) + ("<rdfs:subClassOf rdf:resource='https://www.s3model.com/ns/s3m/s3model_3_1_0.xsd#PartyType'/>\n")
        party_str += padding.rjust(indent + 2) + ("<rdfs:subClassOf rdf:resource='https://www.s3model.com/ns/s3m/s3model/RMC'/>\n")
        party_str += padding.rjust(indent + 2) + ("<rdfs:label>" + escape(self.label.strip()) + "</rdfs:label>\n")
        if len(self.pred_obj_list) != 0:
            for po in self.pred_obj_list:
                party_str += padding.rjust(indent + 2) + ("<" + po.predicate.ns_abbrev.__str__() + ":" + po.predicate.class_name.strip() + " rdf:resource='" + quote(po.object_uri) + "'/>\n")
        party_str += padding.rjust(indent + 2) + ("</rdfs:Class>\n")
        party_str += padding.rjust(indent + 2) + ('</xs:appinfo>\n')
        party_str += padding.rjust(indent + 2) + ("</xs:annotation>\n")
        party_str += padding.rjust(indent + 2) + ("<xs:complexContent>\n")
        party_str += padding.rjust(indent + 4) + ("<xs:restriction base='s3m:PartyType'>\n")
        party_str += padding.rjust(indent + 6) + ("<xs:sequence>\n")
        party_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='1' name='label' type='xs:string' fixed=" + '"' + escape(self.label.strip()) + '"' + "/>\n")

        party_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='0' name='party-name' type='xs:string'/>\n")

        if self.party_ref:
            party_str += padding.rjust(indent + 8) + "<xs:element maxOccurs='1' minOccurs='0' name='party-ref' type='s3m:mc-" + self.party_ref.mcuid + "'/>\n"

        if self.party_details:
            party_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='0' name='party-details' type='s3m:mc-" + self.party_details.mcuid + "'/>\n")

        party_str += padding.rjust(indent + 8) + ("</xs:sequence>\n")
        party_str += padding.rjust(indent + 6) + ("</xs:restriction>\n")
        party_str += padding.rjust(indent + 4) + ("</xs:complexContent>\n")
        party_str += padding.rjust(indent + 2) + ("</xs:complexType>\n\n")
        if self.party_ref:
            party_str += self.party_ref.getModel()
        if self.party_details:
            party_str += self.party_details.getModel()

        return(party_str)

    def getXMLInstance(self, example):
        """
        Return a XML instance for the Party.
        """
        if not self.published:
            raise ValueError("The model must first be published.")
        if example:
            self.party_name = "A. Sample Name"

        indent = 2
        padding = ('').rjust(indent)

        xmlstr = ''
        xmlstr += padding + "<s3m:ms-" + self.mcuid + ">\n"
        xmlstr += padding + "  <label>" + escape(self.label) + "</label>\n"
        if self.party_name is not None:
            xmlstr += padding + "  <party-name>" + escape(self.party_name) + "</party-name>\n"
        if self.party_ref is not None:
            xmlstr += padding + "  <party-ref>\n"
            xmlstr += padding + '    <label>' + self.party_ref.label + '</label>\n'
            xmlstr += padding + '    <link>' + self.party_ref.link + '</link>\n'
            xmlstr += padding + '    <relation>' + self.party_ref.relation + '</relation>\n'
            xmlstr += padding + '    <relation-uri>' + self.party_ref.relation_uri + '</relation-uri>\n'
            xmlstr += padding + "  </party-ref>\n"
    
        if self.party_details is not None:
            xmlstr += padding + "  <party-details>\n"
            xmlstr += padding + "    <label>" + escape(self.party_details.label.strip()) + "</label>\n"
            for adapter in self.party_details.items:
                xmlstr += adapter.value.getXMLInstance(example)

            xmlstr += padding + "  </party-details>\n"
        
        xmlstr += padding + "</s3m:ms-" + self.mcuid + ">\n"
        return(xmlstr)

    def getJSONInstance(self, example):
        """
        Return a JSON instance for the Party.
        """
        xml = self.getXMLInstance(example)
        parsed = xmltodict.parse(xml, encoding='UTF-8', process_namespaces=False)
        return(json.dumps(parsed, indent=2, sort_keys=False))


class AuditType(MetaCommon):
    """
    AuditType provides a mechanism to identify the who/where/when tracking of instances as they move from system to system.
    """

    def __init__(self, label: str):
        """
        The semantic label (name of the model) is required.
        """
        super().__init__(label)

        self._system_id = None
        self._system_user = None
        self._location = None
        self._timestamp = None
        self.cardinality = ('system_user', [0, 1])
        self.cardinality = ('location', [0, 1])

    @property
    def system_id(self):
        """
        Identifier of systems which created or handled the information item. 
        'Systems' can also be defined as an individual application or a data 
        repository in which the data was manipulated.
        """
        return self._system_id

    @system_id.setter
    def system_id(self, v):
        if not self.published:
            if isinstance(v, XdStringType):
                self._system_id = v
            else:
                raise ValueError("the system_id value must be a XdStringType.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def system_user(self):
        """
        User(s) who created, committed, forwarded or otherwise handled the item.
        """
        return self._system_user

    @system_user.setter
    def system_user(self, v):
        if not self.published:
            if isinstance(v, PartyType):
                self._system_user = v
            else:
                raise ValueError("the system_user value must be a PartyType.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def location(self):
        """
        Location information of the particular site/facility within an organisation which handled the item.
        """
        return self._location

    @location.setter
    def location(self, v):
        if not self.published:
            if isinstance(v, ClusterType):
                self._location = v
            else:
                raise ValueError("the location value must be a ClusterType.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def timestamp(self):
        """
        Timestamp of handling the item.
        """
        return self._timestamp

    @timestamp.setter
    def timestamp(self, v):
        if self.published:
            if isinstance(v, datetime):
                self._timestamp = v
            else:
                raise ValueError("the timestamp value must be a datetime.")
        else:
            raise ValueError("The model has not been published.")

    def validate(self):
        """
        Every Type must implement this method.
        """
        if not super(AuditType, self).validate():
            return(False)
        else:
            return(True)

    def getModel(self):
        """
        Return a XML Schema stub for the Audit.
        """
        if not self.published:
            raise ValueError("The model must first be published.")

        if not self.validate():
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + ', ID: ' + self.mcuid + " is not valid.")

        indent = 2
        padding = ('').rjust(indent)
        aud_str = ''

        # Create the datatype
        aud_str += '\n\n' + padding.rjust(indent) + ("<xs:complexType name='mc-" + self.mcuid + "' xml:lang='" + self.language + "'>\n")
        aud_str += padding.rjust(indent + 2) + ("<xs:annotation>\n")
        aud_str += padding.rjust(indent + 2) + ("<xs:documentation>\n")
        aud_str += padding.rjust(indent + 4) + (escape(self.docs) + "\n")
        aud_str += padding.rjust(indent + 2) + ("</xs:documentation>\n")
        # Write the semantic links. There must be the same number of attributes
        # and links or none will be written.
        aud_str += padding.rjust(indent + 2) + ('<xs:appinfo>\n')
        aud_str += padding.rjust(indent + 2) + ("<rdfs:Class rdf:about='mc-" + self.mcuid + "'>\n")
        aud_str += padding.rjust(indent + 2) + ("<rdfs:subClassOf rdf:resource='https://www.s3model.com/ns/s3m/s3model_3_1_0.xsd##AuditType'/>\n")
        aud_str += padding.rjust(indent + 2) + ("<rdfs:subClassOf rdf:resource='https://www.s3model.com/ns/s3m/s3model/RMC'/>\n")
        aud_str += padding.rjust(indent + 2) + ("<rdfs:label>" + escape(self.label.strip()) + "</rdfs:label>\n")
        if len(self.pred_obj_list) != 0:
            for po in self.pred_obj_list:
                pred = po[0]
                obj = po[1]
                xdstr += padding.rjust(indent + 8) + '<' + pred.strip() + ' rdf:resource="' + quote(obj.strip()) + '"/>\n'
        aud_str += padding.rjust(indent + 2) + ("</rdfs:Class>\n")
        aud_str += padding.rjust(indent + 2) + ('</xs:appinfo>\n')
        aud_str += padding.rjust(indent + 2) + ("</xs:annotation>\n")
        aud_str += padding.rjust(indent + 2) + ("<xs:complexContent>\n")
        aud_str += padding.rjust(indent + 4) + ("<xs:restriction base='s3m:AuditType'>\n")
        aud_str += padding.rjust(indent + 6) + ("<xs:sequence>\n")
        aud_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='1' name='label' type='xs:string' fixed=" + '"' + escape(self.label.strip()) + '"' + "/>\n")

        if self.system_id is None:
            raise ValueError("System ID: (XdString) is missing.")
        else:
            aud_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='1' name='system-id' type='s3m:mc-" + str(self.system_id.mcuid) + "'/>\n")

        if self.system_user is None:
            raise ValueError("System User: (Party) " + self.system_user.__str__().strip() + " is missing.")
        else:
            aud_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='0' name='system-user' type='s3m:mc-" + str(self.system_user.mcuid) + "'/>\n")

        if self.location is None:
            raise ValueError("Location: (Cluster) " + self.location.__str__().strip() + " is missing.")
        else:
            aud_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='0' name='location' type='s3m:mc-" + str(self.location.mcuid) + "'/>\n")

        aud_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='1' name='timestamp' type='xs:dateTime'/>\n")

        aud_str += padding.rjust(indent + 8) + ("</xs:sequence>\n")
        aud_str += padding.rjust(indent + 6) + ("</xs:restriction>\n")
        aud_str += padding.rjust(indent + 4) + ("</xs:complexContent>\n")
        aud_str += padding.rjust(indent + 2) + ("</xs:complexType>\n\n")
        aud_str += self.system_id.getModel()
        aud_str += self.system_user.getModel()
        aud_str += self.location.getModel()
        return(aud_str)

    def getXMLInstance(self, example):
        """
        Return a XML instance for the Audit.
        """
        if not self.published:
            raise ValueError("The model must first be published.")
        if example:
            self.timestamp = datetime.now()

        indent = 2
        padding = ('').rjust(indent)
 
        xmlstr = ''
        xmlstr = padding + "<s3m:ms-" + str(self.mcuid) + ">\n"
        xmlstr += padding + "  <label>" + escape(self.label.strip()) + "</label>\n"
        if self.system_id is not None:
            xmlstr += padding + "  <system-id>\n"
            xmlstr += padding + self.system_id.getXMLInstance(example)
            xmlstr += padding + "  </system-id>\n"
    
        if self.system_user is not None:
            xmlstr += padding + "  <system-user>\n"
            xmlstr += padding + self.system_user.getXMLInstance(example)
            xmlstr += padding + "  </system-user>\n"
    
        if self.location is not None:
            xmlstr += padding + "  <location>\n"
            xmlstr += padding + self.location.getXMLInstance(example)
            xmlstr += padding + "  </location>\n"
        if self.timestamp is not None:
            xmlstr += padding + "  <timestamp>" + self.timestamp.isoformat() + "</timestamp>\n"
        xmlstr += padding + "</s3m:ms-" + str(self.mcuid) + ">\n"
        
        return(xmlstr)

    def getJSONInstance(self, example):
        """
        Return a JSON instance for the Audit.
        """
        xml = self.getXMLInstance(example)
        parsed = xmltodict.parse(xml, encoding='UTF-8', process_namespaces=False)
        return(json.dumps(parsed, indent=2, sort_keys=False))

class AttestationType(MetaCommon):
    """
    Record an attestation by a party of the DM content. 
    The type of attestation is recorded by the reason attribute, 
    which my be coded from a controlled vocabulary.
    """

    def __init__(self, label: str):
        """
        The semantic label (name of the model) is required.
        """
        super().__init__(label)

        self._view = None
        self._proof = None
        self._reason = None
        self._committer = None
        self._committed = None
        self._pending = True
        self.cardinality = ('view', [0, 1])
        self.cardinality = ('proof', [0, 1])
        self.cardinality = ('reason', [0, 1])
        self.cardinality = ('committer', [0, 1])
        self.cardinality = ('committed', [0, 1])

    @property
    def view(self):
        """
        Optional visual representation of content attested e.g. screen image.
        """
        return self._view

    @view.setter
    def view(self, v):
        if not self.published:
            if isinstance(v, XdFileType):
                self._view = v
            else:
                self._view = None
                raise TypeError("The view value must be a XdFileType.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def proof(self):
        """
        Proof of attestation such as an GPG signature.
        """
        return self._proof

    @proof.setter
    def proof(self, v):
        if not self.published:
            if isinstance(v, XdFileType):
                self._proof = v
            else:
                self._proof = None
                raise TypeError("The proof value must be a XdFileType.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def reason(self):
        """
        Reason of this attestation. Usually coded from a standardized vocabulary.        
        """
        return self._reason

    @reason.setter
    def reason(self, v):
        if not self.published:
            if isinstance(v, XdStringType):
                self._reason = v
            else:
                self._reason = None
                raise TypeError("The reason value must be a XdStringType.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def committer(self):
        """
        Identity of person who committed the item.        
        """
        return self._committer

    @committer.setter
    def committer(self, v):
        if not self.published:
            if isinstance(v, PartyType):
                self._committer = v
            else:
                self._committer = None
                raise TypeError("The committer value must be a PartyType.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def committed(self):
        """
        Timestamp of committal of the item.        
        """
        return self._committed

    @committed.setter
    def committed(self, v):
        if self.published:
            if isinstance(v, datetime):
                self._committed = v
            else:
                self._committed = None
                raise TypeError("The committed value must be a datetime.")
        else:
            raise ValueError("The model has not been published.")

    @property
    def pending(self):
        """
        True if this attestation is outstanding; 'false' means it has been completed.
        """
        return self._pending

    @pending.setter
    def pending(self, v):
        if self.published:
            if isinstance(v, bool):
                self._pending = v
            else:
                self._pending = None
                raise TypeError("The pending value must be a boolean.")
        else:
            raise ValueError("The model has not been published.")

    def validate(self):
        """
        Every Type must implement this method.
        """
        if not super(AttestationType, self).validate():
            return(False)
        else:
            return(True)

    def getModel(self):
        """
        Return a XML Schema stub for the Attestation.
        """
        if not self.published:
            raise ValueError("The model must first be published.")

        if not self.validate():
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + ', ID: ' + self.mcuid + " is not valid.")

        indent = 2
        padding = ('').rjust(indent)
        att_str = ''

        # Create the datatype
        att_str += '\n\n' + padding.rjust(indent) + ("<xs:complexType name='mc-" + self.mcuid + "' xml:lang='" + self.language + "'>\n")
        att_str += padding.rjust(indent + 2) + ("<xs:annotation>\n")
        att_str += padding.rjust(indent + 2) + ("<xs:documentation>\n")
        att_str += padding.rjust(indent + 4) + (escape(self.docs) + "\n")
        att_str += padding.rjust(indent + 2) + ("</xs:documentation>\n")
        # Write the semantic links. There must be the same number of attributes
        # and links or none will be written.
        att_str += padding.rjust(indent + 2) + ('<xs:appinfo>\n')
        att_str += padding.rjust(indent + 2) + ("<rdfs:Class rdf:about='mc-" + self.mcuid + "'>\n")
        att_str += padding.rjust(indent + 2) + ("<rdfs:subClassOf rdf:resource='https://www.s3model.com/ns/s3m/s3model_3_1_0.xsd#AttestationType'/>\n")
        att_str += padding.rjust(indent + 2) + ("<rdfs:subClassOf rdf:resource='https://www.s3model.com/ns/s3m/s3model/RMC'/>\n")
        att_str += padding.rjust(indent + 2) + ("<rdfs:label>" + escape(self.label.strip()) + "</rdfs:label>\n")
        if len(self.pred_obj_list) != 0:
            for po in self.pred_obj_list:
                att_str += padding.rjust(indent + 2) + ("<" + po.predicate.ns_abbrev.__str__() + ":" + po.predicate.class_name.strip() + " rdf:resource='" + quote(po.object_uri) + "'/>\n")
        att_str += padding.rjust(indent + 2) + ("</rdfs:Class>\n")
        att_str += padding.rjust(indent + 2) + ('</xs:appinfo>\n')
        att_str += padding.rjust(indent + 2) + ("</xs:annotation>\n")
        att_str += padding.rjust(indent + 2) + ("<xs:complexContent>\n")
        att_str += padding.rjust(indent + 4) + ("<xs:restriction base='s3m:AttestationType'>\n")
        att_str += padding.rjust(indent + 6) + ("<xs:sequence>\n")
        att_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='1' name='label' type='xs:string' fixed=" + '"' + escape(self.label.strip()) + '"' + "/>\n")

        if self.view is not None:
            att_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['view'][0]) + "' name='view' type='s3m:mc-" + str(self.view.mcuid) + "'/> \n")

        if self.proof is not None:
            att_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['proof'][0]) + "' name='proof' type='s3m:mc-" + str(self.proof.mcuid) + "'/> \n")

        if self.reason is not None:
            att_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['reason'][0]) + "' name='reason' type='s3m:mc-" + str(self.reason.mcuid) + "'/> \n")

        if self.committer is not None:
            att_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['committer'][0]) + "' name='committer' type='s3m:mc-" + str(self.committer.mcuid) + "'/>\n")

        att_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['committed'][0]) + "' name='committed' type='xs:dateTime'/>\n")
        att_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='1' default='true' name='pending' type='xs:boolean'/>\n")
        att_str += padding.rjust(indent + 8) + ("</xs:sequence>\n")
        att_str += padding.rjust(indent + 6) + ("</xs:restriction>\n")
        att_str += padding.rjust(indent + 4) + ("</xs:complexContent>\n")
        att_str += padding.rjust(indent + 2) + ("</xs:complexType>\n\n")
        if self.view is not None:
            att_str += self.view.getModel()
        if self.proof is not None:
            att_str += self.proof.getModel()
        if self.reason is not None:
            att_str += self.reason.getModel()
        if self.committer is not None:
            att_str += self.committer.getModel()

        return(att_str)

    def getXMLInstance(self, example):
        """
        Return a XML instance for the Attestation.
        """
        if not self.published:
            raise ValueError("The model must first be published.")
        if example:
            self.committed = datetime.now()
            
        indent = 2
        padding = ('').rjust(indent)
        xmlstr = ''
        xmlstr += padding + "<s3m:ms-" + self.mcuid + ">\n"
        xmlstr += "<label>" + escape(self.label.strip()) + "</label>\n"
        if self.view is not None:
            xmlstr += padding + "<view>\n"
            xmlstr += padding + self.view.getXMLInstance(example)
            xmlstr += padding + "</view>\n"
        if self.proof is not None:
            xmlstr += padding + "<proof>\n"
            xmlstr += padding + self.proof.getXMLInstance(example)
            xmlstr += padding + "</proof>\n"
        if self.reason is not None:
            xmlstr += padding + "<reason>\n"
            xmlstr += padding + self.reason.getXMLInstance(example)
            xmlstr += padding + "</reason>\n"
        if self.committer is not None:
            xmlstr += padding + "<committer>\n"
            xmlstr += padding + self.committer.getXMLInstance(example)
            xmlstr += padding + "</committer>\n"
        if self.committed is not None:
            xmlstr += padding + "  <committed>" + self.committed.isoformat() + "</committed>\n"
        xmlstr += padding + "  <pending>" + str(self.pending).lower() + "</pending>\n"
        xmlstr += padding + "</s3m:ms-" + self.mcuid + ">\n"

        return(xmlstr)

    def getJSONInstance(self, example):
        """
        Return a JSON instance for the Attestation.
        """
        xml = self.getXMLInstance(example)
        parsed = xmltodict.parse(xml, encoding='UTF-8', process_namespaces=False)
        return(json.dumps(parsed, indent=2, sort_keys=False))

class ParticipationType(MetaCommon):
    """
    Model of a participation of a Party (any Actor or Role) in an activity. 
    Used to represent any participation of a Party in some activity, which is 
    not explicitly in the model, e.g. assisting nurse. 
    Can be used to record past or future participations.
    """

    def __init__(self, label: str):
        """
        The semantic label (name of the model) is required.
        """
        super().__init__(label)
        self._performer = None
        self._function = None
        self._mode = None
        self._start = None
        self._end = None
        self.cardinality = ('performer', [0, 1])
        self.cardinality = ('function', [0, 1])
        self.cardinality = ('mode', [0, 1])
        self.cardinality = ('start', [0, 1])
        self.cardinality = ('end', [0, 1])

    @property
    def performer(self):
        """
        The id and possibly demographic system link of the party participating in the activity.
        """
        return self._performer

    @performer.setter
    def performer(self, v):
        if not self.published:
            if isinstance(v, PartyType):
                self._performer = v
            else:
                self._performer = None
                raise TypeError("The performer value must be a PartyType.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def function(self):
        """
        The function of the Party in this participation (note that a given 
        party might participate in more than one way in a particular activity). 
        
        In some applications this might be called a Role.
        """
        return self._function

    @function.setter
    def function(self, v):
        if not self.published:
            if isinstance(v, XdStringType):
                self._function = v
            else:
                self._function = None
                raise TypeError("The function value must be a XdStringType.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def mode(self):
        """
        The mode of the performer / activity interaction, e.g. present, by 
        telephone, by email etc. 
        
        If the participation is by device or software it may contain a protocol 
        standard or interface definition.
        """
        return self._mode

    @mode.setter
    def mode(self, v):
        if not self.published:
            if isinstance(v, XdStringType):
                self._mode = v
            else:
                self._mode = None
                raise TypeError("The mode value must be a XdStringType.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def start(self):
        """
        The beginning datetime when the participation took place.
        """
        return self._start

    @start.setter
    def start(self, v):
        if self.published:
            if isinstance(v, datetime):
                self._start = v
            else:
                self._start = None
                raise TypeError("The start value must be a datetime.")
        else:
            raise ValueError("The model has not been published.")

    @property
    def end(self):
        """
        The ending datetime when the participation took place.
        """
        return self._end

    @end.setter
    def end(self, v):
        if self.published:
            if isinstance(v, datetime):
                self._end = v
            else:
                self._end = None
                raise TypeError("The end value must be a datetime.")
        else:
            raise ValueError("The model has not been published.")

    def validate(self):
        """
        Every Type must implement this method.
        """
        if not super(ParticipationType, self).validate():
            return(False)
        else:
            return(True)

    def getModel(self):
        """
        Return a XML Schema stub for the Participation.
        """
        if not self.published:
            raise ValueError("The model must first be published.")

        if not self.validate():
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + ', ID: ' + self.mcuid + " is not valid.")

        indent = 2
        padding = ('').rjust(indent)
        ptn_str = ''

        # Create the datatype
        ptn_str += '\n\n' + padding.rjust(indent) + ("<xs:complexType name='mc-" + self.mcuid + "' xml:lang='" + self.language + "'> \n")
        ptn_str += padding.rjust(indent + 2) + ("<xs:annotation>\n")
        ptn_str += padding.rjust(indent + 2) + ("<xs:documentation>\n")
        ptn_str += padding.rjust(indent + 4) + (escape(self.docs) + "\n")
        ptn_str += padding.rjust(indent + 2) + ("</xs:documentation>\n")
        # Write the semantic links. There must be the same number of attributes
        # and links or none will be written.
        ptn_str += padding.rjust(indent + 2) + ('<xs:appinfo>\n')
        ptn_str += padding.rjust(indent + 2) + ("<rdfs:Class rdf:about='mc-" + self.mcuid + "'>\n")
        ptn_str += padding.rjust(indent + 2) + ("<rdfs:subClassOf rdf:resource='https://www.s3model.com/ns/s3m/s3model_3_1_0.xsd#ParticipationType'/>\n")
        ptn_str += padding.rjust(indent + 2) + ("<rdfs:subClassOf rdf:resource='https://www.s3model.com/ns/s3m/s3model/RMC'/>\n")
        ptn_str += padding.rjust(indent + 2) + ("<rdfs:label>" + escape(self.label.strip()) + "</rdfs:label>\n")
        if len(self.pred_obj_list) > 0:  # are there additional predicate-object definitions?
            for po in self.pred_obj_list:
                pred = po[0]
                obj = po[1]
                ptn_str += padding.rjust(indent + 8) + '<' + pred.strip() + ' rdf:resource="' + quote(obj.strip()) + '"/>\n'
        ptn_str += padding.rjust(indent + 2) + ("</rdfs:Class>\n")
        ptn_str += padding.rjust(indent + 2) + ('</xs:appinfo>\n')
        ptn_str += padding.rjust(indent + 2) + ("</xs:annotation>\n")
        ptn_str += padding.rjust(indent + 2) + ("<xs:complexContent>\n")
        ptn_str += padding.rjust(indent + 4) + ("<xs:restriction base='s3m:ParticipationType'>\n")
        ptn_str += padding.rjust(indent + 6) + ("<xs:sequence>\n")
        ptn_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='1' name='label' type='xs:string' fixed=" + '"' + escape(self.label.strip()) + '"' + "/>\n")
    
        # Participation
        if self.performer is not None:
            ptn_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['performer'][0]) + "' name='performer' type='s3m:mc-" + str(self.performer.mcuid) + "'/>\n")

        if self.function is not None:
            ptn_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['function'][0]) + "' name='function' type='s3m:mc-" + str(self.function.mcuid) + "'/>\n")

        if self.mode is not None:
            ptn_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['mode'][0]) + "' name='mode' type='s3m:mc-" + str(self.mode.mcuid) + "'/> \n")

        ptn_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['start'][0]) + "' name='start' type='xs:dateTime'/>\n")
        ptn_str += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['end'][0]) + "' name='end' type='xs:dateTime'/>\n")

        ptn_str += padding.rjust(indent + 8) + ("</xs:sequence>\n")
        ptn_str += padding.rjust(indent + 6) + ("</xs:restriction>\n")
        ptn_str += padding.rjust(indent + 4) + ("</xs:complexContent>\n")
        ptn_str += padding.rjust(indent + 2) + ("</xs:complexType>\n\n")
        
        if self.performer is not None:
            ptn_str += self.performer.getModel()
        if self.function is not None:
            ptn_str += self.function.getModel()
        if self.mode is not None:
            ptn_str += self.mode.getModel()

        return(ptn_str)

    def getXMLInstance(self, example):
        """
        Return a XML instance for the Participation.
        """
        if not self.published:
            raise ValueError("The model must first be published.")
        if example:
            pass
        

        indent = 2
        padding = ('').rjust(indent)

        xmlstr = ''
        xmlstr += "<s3m:ms-" + self.mcuid + ">\n"
        xmlstr += padding + "  <label>" + escape(self.label.strip()) + "</label>\n"
        
        if self.performer is not None:
            xmlstr += padding + "<performer>\n"
            xmlstr += padding + "  <label>" + escape(self.performer.label) + "</label>\n"
            if self.performer.party_name is not None:
                xmlstr += padding + "  <party-name>" + escape(self.performer.party_name) + "</party-name>\n"
            if self.performer.party_ref is not None:
                xmlstr += padding + "  <party-ref>\n"
                xmlstr += padding + '    <label>' + self.performer.party_ref.label + '</label>\n'
                xmlstr += padding + '    <link>' + self.performer.party_ref.link + '</link>\n'
                xmlstr += padding + '    <relation>' + self.performer.party_ref.relation + '</relation>\n'
                xmlstr += padding + '    <relation-uri>' + self.performer.party_ref.relation_uri + '</relation-uri>\n'
                xmlstr += padding + "  </party-ref>\n"
        
            if self.performer.party_details is not None:
                xmlstr += padding + "  <party-details>\n"
                xmlstr += padding + "    <label>" + escape(self.performer.party_details.label.strip()) + "</label>\n"
                for adapter in self.performer.party_details.items:
                    xmlstr += padding + adapter.value.getXMLInstance(example)
    
                xmlstr += padding + "  </party-details>\n"
            
            xmlstr += padding + "</performer>\n"
    
        if self.function is not None:
            xmlstr += padding + "<function>\n"
            xmlstr += padding + self.function.getXMLInstance(example)
            xmlstr += padding + "</function>\n"
    
        if self.mode is not None:
            xmlstr += padding + "<mode>\n"
            xmlstr += padding + self.mode.getXMLInstance(example)
            xmlstr += padding + "</mode>\n"
    
        if self.start is not None:
            xmlstr += padding + "  <start>" + str(self.start) + "</start>\n"
        if self.end is not None:
            xmlstr += padding + "  <end>" + str(self.end) + "</end>\n"
        
        xmlstr += padding + "</s3m:ms-" + self.mcuid + ">\n"
        return(xmlstr)

    def getJSONInstance(self, example):
        """
        Return a JSON instance for the Participation.
        """
        xml = self.getXMLInstance(example)
        parsed = xmltodict.parse(xml, encoding='UTF-8', process_namespaces=False)
        return(json.dumps(parsed, indent=2, sort_keys=False))

