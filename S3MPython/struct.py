"""
Structural items.

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
from abc import ABC, abstractmethod
from typing import ByteString, Dict, List, Tuple, Iterable
from xml.sax.saxutils import escape
from urllib.parse import quote
import json

import xmltodict
from cuid import cuid
from validator_collection import checkers

from .xdt import XdAnyType
from .errors import ValidationError, PublicationError


class ItemType(ABC):
    """
    The abstract parent of ClusterType and XdAdapterType 
    structural representation types.
    """

    @abstractmethod
    def __init__(self):
        self._published = False

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
        

    def __str__(self):
        if self.validate():
            return(self.__class__.__name__ + ' : ' + self.label + ', ID: ' + self.mcuid + " Published: " + str(self._published))
        else:
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + ', ID: ' + self.mcuid + " is not valid.")

    def validate(self):
        return(True)


class XdAdapterType(ItemType):
    """
    The leaf variant of Item, to which any XdAnyType subtype instance is 
    attached for use in a Cluster. 

    The unique ID for the adapter is part of the value (XdType).
    """

    def __init__(self):
        super().__init__()                
        self._value = None
        self._mcuid = None
        self.label = 'Empty XdAdapter'

    @property
    def mcuid(self):
        """
        The unique identifier of the component.
        """
        return self._mcuid

    @property
    def value(self):
        """
        The XdType contained in an XdAdapter.
        """
        return self._value

    @value.setter
    def value(self, v):
        if not self.published:
            if v.published:
                if isinstance(v, XdAnyType) and self._value == None:
                    self._value = v
                    self._value.adapter = True
                    self._mcuid = self._value.acuid 
                    self.label = 'XdAdapter for ' + self.value.label
                    self._published = True  # automatically publish the adapter when an item is added
                else:
                    raise ValueError("the value must be a XdAnyType subtype. A XdAdapter can only contain one XdType.")
            else:
                raise ValueError("The model has been published and cannot be edited.")
        else:
            raise ValueError(v.__str__() + " has not been published and therefore cannot be wrapped in a XdAdapter.")

    def validate(self):
        """
        Every Type must implement this method.
        """
        if not super(XdAdapterType, self).validate():
            return(False)
        else:
            return(True)

 
    def getModel(self):
        """
        Return a XML Schema stub for the adapter.
        """
        if not self.published:
            raise ValueError("The model must first be published.")

        if not self.validate():
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + ', ID: ' + self.mcuid + " is not valid.")

        indent = 2
        padding = ('').rjust(indent)
        xdstr = ''
        xdstr += padding.rjust(indent) + '\n<xs:element name="ms-' + self.mcuid + '" substitutionGroup="s3m:Items" type="s3m:mc-' + self.mcuid + '"/>\n'
        xdstr += padding.rjust(indent) + '<xs:complexType name="mc-' + self.mcuid + '">\n'
        xdstr += padding.rjust(indent + 2) + '<xs:complexContent>\n'
        xdstr += padding.rjust(indent + 4) + '<xs:restriction base="s3m:XdAdapterType">\n'
        xdstr += padding.rjust(indent + 6) + '<xs:sequence>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="unbounded" minOccurs="0" ref="s3m:ms-' + self.value.mcuid + '"/>\n'
        xdstr += padding.rjust(indent + 6) + '</xs:sequence>\n'
        xdstr += padding.rjust(indent + 4) + '</xs:restriction>\n'
        xdstr += padding.rjust(indent + 2) + '</xs:complexContent>\n'
        xdstr += padding.rjust(indent) + '</xs:complexType>\n\n'
        xdstr += self.value.getModel()
        return(xdstr)


class ClusterType(ItemType):
    """
    The grouping component, which may contain further instances of itself or 
    any eXtended datatype, in an ordered list. 

    This component serves as the root component for arbitrarily complex 
    structures.
    """

    def __init__(self, label):
        """
        The semantic label (name of the model) is required.
        """
        super().__init__()        
        self._mcuid = cuid()  # model cuid
        self._label = label
        self._items = []
        self._docs = ''
        self._definition_url = ''
        self._pred_obj_list = []

        if checkers.is_string(label, 2):
            self._label = label
        else:
            raise TypeError('"label" must be a string type and at least 2 characters long. Not a ', type(label))

    @property
    def label(self):
        """
        The semantic name of the ClusterType.
        """
        return self._label

    @property
    def mcuid(self):
        """
        The unique identifier of the component.
        """
        return self._mcuid

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
                self._docs += '\n        Definition: ' + quote(v)
            else:
                raise ValueError("the Definition URL value must be a valid URL.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    @property
    def items(self):
        """
        The items contained in a Cluster.
        """
        return self._items

    @items.setter
    def items(self, v):
        if not self.published:
            if isinstance(v, ItemType):
                if v.published:
                    self._items.append(v)
                else:
                    raise PublicationError("The item " + v.label + " must first be published.")
            else:
                if isinstance(v, (XdAnyType, ClusterType)):
                    raise TypeError("XdType items in a ClusterType must be wrapped in an XdAdapterType.")
                else:
                    raise TypeError("items in a ClusterType must be of type ItemType.")
        else:
            raise ValueError("The model has been published and cannot be edited.")

    def validate(self):
        """
        Every Type must implement this method.
        """
        if not super(ClusterType, self).validate():
            return(False)
        elif not checkers.is_url(self.definition_url):
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + " failed validation: definition_url is invalid")
        elif len(self.label) < 2:
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + " failed validation: missing or short label")
        elif len(self.items) < 1:
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + " failed validation: missing items")
        else:
            return(True)


    def getModel(self):
        """
        Return a XML Schema stub for the Cluster.
        """
        if not self.published:
            raise ValueError("The model must first be published.")

        self.validate()
        indent = 2
        padding = ('').rjust(indent)
        xdstr = ''
        xdstr += padding.rjust(indent) + '\n<xs:element name="ms-' + self.mcuid + '" substitutionGroup="s3m:Item" type="s3m:mc-' + self.mcuid + '"/>\n'
        xdstr += padding.rjust(indent) + '<xs:complexType name="mc-' + self.mcuid + '">\n'
        xdstr += padding.rjust(indent + 2) + '<xs:annotation>\n'
        xdstr += padding.rjust(indent + 4) + '<xs:documentation>\n'
        xdstr += padding.rjust(indent + 6) + escape(self.docs.strip()) + '\n'
        xdstr += padding.rjust(indent + 4) + '</xs:documentation>\n'
        xdstr += padding.rjust(indent + 4) + '<xs:appinfo>\n'

        # add RDF
        xdstr += padding.rjust(indent + 6) + '<rdfs:Class rdf:about="mc-' + self.mcuid + '">\n'
        xdstr += padding.rjust(indent + 8) + '<rdfs:subClassOf rdf:resource="https://www.s3model.com/ns/s3m/s3model_3_1_0.xsd#ClusterType"/>\n'
        xdstr += padding.rjust(indent + 8) + '<rdfs:subClassOf rdf:resource="https://www.s3model.com/ns/s3m/s3model/RMC"/>\n'
        xdstr += padding.rjust(indent + 8) + '<rdfs:isDefinedBy rdf:resource="' + quote(self.definition_url.strip()) + '"/>\n'
        if len(self.pred_obj_list) > 0:  # are there additional predicate-object definitions?
            for po in self.pred_obj_list:
                pred = po[0]
                obj = po[1]
                xdstr += padding.rjust(indent + 8) + '<' + pred.strip() + ' rdf:resource="' + quote(obj.strip()) + '"/>\n'
        xdstr += padding.rjust(indent + 6) + '</rdfs:Class>\n'
        xdstr += padding.rjust(indent + 4) + '</xs:appinfo>\n'
        xdstr += padding.rjust(indent + 2) + '</xs:annotation>\n'
        xdstr += padding.rjust(indent + 2) + '<xs:complexContent>\n'
        xdstr += padding.rjust(indent + 4) + '<xs:restriction base="s3m:ClusterType">\n'
        xdstr += padding.rjust(indent + 6) + '<xs:sequence>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="1" name="label" type="xs:string" fixed="' + self.label.strip() + '"/>\n'
        for item in self.items:
            xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="0" ref="s3m:ms-' + item.value.acuid + '"/>\n'
        xdstr += padding.rjust(indent + 6) + '</xs:sequence>\n'
        xdstr += padding.rjust(indent + 4) + '</xs:restriction>\n'
        xdstr += padding.rjust(indent + 2) + '</xs:complexContent>\n'
        xdstr += padding.rjust(indent) + '</xs:complexType>\n\n'
        for item in self.items:
            xdstr += item.getModel()

        return(xdstr)


    def getXMLInstance(self, example):
        """
        Return an XML fragment for this model.
        """
        indent = '  '
        xmlstr = ''
 
        xmlstr += indent + "<s3m:ms-" + self.mcuid + ">\n"
        xmlstr += indent + "  <label>" + escape(self.label.strip()) + "</label>\n"
        for adapter in self.items:
            xmlstr += adapter.value.getXMLInstance(example)
        xmlstr += indent + "</s3m:ms-" + self.mcuid + ">\n"
        return(xmlstr)
    
    def getJSONInstance(self, example):
        """
        Return a JSON instance for the Participation.
        """
        xml = self.getXMLInstance(example)
        parsed = xmltodict.parse(xml, encoding='UTF-8', process_namespaces=False)
        return(json.dumps(parsed, indent=2, sort_keys=False))
    