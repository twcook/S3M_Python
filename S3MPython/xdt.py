"""
Defines the S3Model reference model in Python 3.7
Version 3.1.0
This implementation is not a strict model of the RM.
It also contains functionality to manage constraints that are
built into the XML Schema parsers.

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
import re
import json
import numbers
from random import randint, choice, uniform, randrange, random
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from collections import OrderedDict
from abc import ABC, abstractmethod
from xml.sax.saxutils import escape
from urllib.parse import quote
from base64 import b64encode
from typing import ByteString, Dict, List, Tuple, Iterable

import xmltodict
import pytz
import exrex
from cuid import cuid
from validator_collection import checkers
from lxml import etree as ET

from .ev import ExceptionalValue
from .errors import ValidationError, PublicationError
from .utils import get_latlon, random_dtstr, valid_cardinality, reg_ns, fetch_acs
from .settings import get_acs, ACSFILE

ACS = get_acs(ACSFILE)

# globally register namespaces
ns_dict = reg_ns()
for abbrev in ns_dict.keys():
    ET.register_namespace(abbrev, ns_dict[abbrev])

class XdAnyType(ABC):
    """
    Serves as an abstract common ancestor of all eXtended data-types (Xd*)
    in S3Model.
    """

    # TODO: Implement complete constraint checking.

    @abstractmethod
    def __init__(self, label: str):
        """
        Initialization for Xd* datatypes in S3Model.

        The semantic label (name of the model) is required.
        """
        self._mcuid = cuid()  # model cuid
        self._acuid = cuid()  # adapter cuid
        self._label = ''

        self._published = False
        self._xdtype = None
        self._adapter = False  # flag is set True by a XdAdapter for use in a Cluster, otherwise it is false
        self._docs = ''
        self._definition_url = ''
        self._pred_obj_list = []
        self._act = None
        self._ev = []
        self._vtb = None
        self._vte = None
        self._tr = None
        self._modified = None
        self._latitude = None
        self._longitude = None
        self._cardinality = {'act': [0, 1], 'ev': [0, None], 'vtb': [0, 1], 'vte': [0, 1],
                             'tr': [0, 1], 'modified': [0, 1], 'location': [0, 1]}

        if checkers.is_string(label, minimum_length=2) and not self._published:
            self._label = label
        else:
            raise TypeError('"label" must be a string type of at least 2 characters. Not a ', type(label))

    @property
    def cardinality(self):
        """
        The cardinality status values.

        The setter method can be called by each subclass to add cardinality
        values for each element or change the defaults.
        Some elements cardinality may not be changed.
        Ex: XdBoolean elements are not modifiable.

        The cardinality dictionary uses a string representation of each
        property name and a list as the value.

        The value passed into the setter is a tuple with v[0] as a string (key) and
        v[1] as a list containing an integer set representing the
        (minimum, maximum) values. The entire value list is replaced in the dictionary.

        Examples
        --------

        ('vtb', [1,1]) will set the vtb value to be required.


        NOTES
        -----

        The cardinality for latitude and longitude are combined into one
        setting called 'location'.

        The Python value of 'None' represents the 'unbounded' XML Schema value.
        None is converted to Decimal('Infinity') for comparisons.
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
                    raise TypeError("The cardinality values must be integers or None.")
            else:
                raise ValueError("The cardinality value is malformed. It must be a tuple of a string and a list of two integers.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def mcuid(self):
        """
        The unique identifier of the component.
        """
        return self._mcuid

    @property
    def acuid(self):
        """
        The unique identifier of the wrapping XdAdapter of the component.
        """
        return self._acuid

    @property
    def label(self):
        """
        The semantic name of the component.

        REQUIRED
        """
        return self._label

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
    def adapter(self):
        """
        When True, creates an XdAdapterType wrapper.
        """
        return self._adapter

    @adapter.setter
    def adapter(self, v: bool):
        if isinstance(v, bool):
            self._adapter = v
        else:
            raise ValueError("the adapter value must be a boolean.")

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
            raise PublicationError("The model has been published and cannot be edited.")

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
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def definition_url(self):
        """
        The primary definition URL for the model.
        Cannot be an IP address.

        REQUIRED
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
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def act(self):
        """
        Access Control Tag.

        If this is used it must contain a valid term from the Access Control System linked
        to by the containing Data Model 'acs' attribute. It is available as the ACS imported
        from s3m_dm.
        """
        return self._act

    @act.setter
    def act(self, v: str):
        if self.published:
            if checkers.is_string(v):
                if v in ACS:
                    self._act = v
                else:
                    raise ValueError("The act value must be in the Access Control System list.")
            else:
                raise ValueError("the Access Control Tag value must be a string.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def ev(self):
        """
        In an invalid instance, the application can indicate here why data is
        missing or invalid. This is a list of ExceptionalValue subclasses.

        The sub-types are based on ISO 21090 NULL Flavors entries, with
        additions noted from real-world usage.
        """
        return self._ev

    @ev.setter
    def ev(self, v):
        if self.published:
            if checkers.is_type(v, 'ExceptionalValue'):
                self._ev.append(v)
            else:
                raise ValueError("the ev value must be an ExceptionalValue.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def vtb(self):
        """
        Valid Time Begin. If present this must be a valid datetime including timezone.
        It is used to indicate the beginning time that information is considered valid.
        """
        return self._vtb

    @vtb.setter
    def vtb(self, v):
        if self.published:
            if checkers.is_datetime(v):
                self._vtb = v
            else:
                raise ValueError("the Valid Time Begin value must be a datetime.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def vte(self):
        """
        Valid Time End. If present this must be a valid date-time including timezone.
        It is used to indicate the ending time that information is considered valid
        or the time the information expired or will expire.
        """
        return self._vte

    @vte.setter
    def vte(self, v):
        if self.published:
            if checkers.is_datetime(v):
                self._vte = v
            else:
                raise ValueError("the Valid Time End value must be a datetime.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def tr(self):
        """
        Time Recorded. If present this must be a valid date-time.
        It is used to indicate the initial date and time the data was recorded.
        """
        return self._tr

    @tr.setter
    def tr(self, v):
        if self.published:
            if checkers.is_datetime(v):
                self._tr = v
            else:
                raise ValueError("the Time Recorded value must be a datetime.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def modified(self):
        """
        Time Modified. If present this must be a valid date-time stamp.
        It is used to indicate the date and time the data was last changed.
        """
        return self._modified

    @modified.setter
    def modified(self, v):
        if self.published:
            if checkers.is_datetime(v):
                self._modified = v
            else:
                raise ValueError("the Modified value must be a datetime.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def latitude(self):
        """
        Latitude in decimal format. Value range -90.000000 to 90.000000.
        """
        return self._latitude

    @latitude.setter
    def latitude(self, v):
        if self.published:
            if checkers.is_decimal(v, minimum=-90.00, maximum=90.00):
                self._latitude = v
            else:
                raise ValueError("the Latitude value must be a decimal between -90.00 and 90.00.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def longitude(self):
        """
        Longitude in decimal format. Value range -180.000000 to 180.000000.
        """
        return self._longitude

    @longitude.setter
    def longitude(self, v):
        if self.published:
            if checkers.is_decimal(v, minimum=-180.00, maximum=180.00):
                self._longitude = v
            else:
                raise ValueError("the Longitude value must be a decimal between -180.00 and 180.00.")
        else:
            raise PublicationError("The model has not been published.")

    def __str__(self):
        if self.validate():
            return(self.__class__.__name__ + ' : ' + self.label + ', ID: ' + self.mcuid + " Published: " + str(self._published))
        else:
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + ', ID: ' + self.mcuid + " is not valid.")

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not checkers.is_url(self.definition_url):
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + " - failed validation: definition_url is invalid\n" + str(self.definition_url))
        elif not isinstance(self.label, str) or len(self.label) < 2:
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + " - failed validation: label is too short or missing\n" + str(self.label))
        else:
            return(True)

    def getModel(self):
        """
        Return a XML Schema stub for Xd Types.
        """
        if not self.published:
            raise PublicationError("The model must first be published.")

        self.validate()

        indent = 2
        padding = ('').rjust(indent)
        xdstr = ''
        if self.adapter:
            xdstr += padding.rjust(indent) + '<xs:element name="ms-' + self.mcuid + '" substitutionGroup="s3m:XdAdapter-value" type="s3m:mc-' + self.mcuid + '"/>\n'
        else:
            # Get the class to use for the substitution element. Strip off the leading type information.
            sg = type(self)
            sg = str(sg)
            sg = sg.replace("<class 'S3MPython.xdt.","")
            sg = sg.replace("'>", '')
            xdstr += padding.rjust(indent) + '<xs:element name="ms-' + self.mcuid + '" substitutionGroup="s3m:' + sg + '" type="s3m:mc-' + self.mcuid + '"/>\n'

        xdstr += padding.rjust(indent) + '<xs:complexType name="mc-' + self.mcuid + '">\n'
        xdstr += padding.rjust(indent + 2) + '<xs:annotation>\n'
        xdstr += padding.rjust(indent + 4) + '<xs:documentation>\n'
        xdstr += padding.rjust(indent + 6) + escape(self.docs.strip()) + '\n'
        xdstr += padding.rjust(indent + 4) + '</xs:documentation>\n'
        xdstr += padding.rjust(indent + 4) + '<xs:appinfo>\n'

        # add RDF
        xdstr += padding.rjust(indent + 6) + '<rdfs:Class rdf:about="mc-' + self.mcuid + '">\n'
        xdstr += padding.rjust(indent + 8) + '<rdfs:subClassOf rdf:resource="https://www.s3model.com/ns/s3m/s3model_3_1_0.xsd#' + self._xdtype + '"/>\n'
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
        xdstr += padding.rjust(indent + 4) + '<xs:restriction base="s3m:' + self._xdtype + '">\n'
        xdstr += padding.rjust(indent + 6) + '<xs:sequence>\n'
        # XdAny
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="1" name="label" type="xs:string" fixed="' + self.label.strip() + '"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['act'][0]) + '" name="act" type="xs:string"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="unbounded" minOccurs="0" ref="s3m:ExceptionalValue"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['vtb'][0]) + '" name="vtb" type="xs:dateTime"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['vte'][0]) + '" name="vte" type="xs:dateTime"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['tr'][0]) + '" name="tr" type="xs:dateTime"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['modified'][0]) + '" name="modified" type="xs:dateTime"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['location'][0]) + '" name="latitude" type="s3m:lattype"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['location'][0]) + '" name="longitude" type="s3m:lontype"/>\n'

        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an XML fragment for this model.
        """
        if not self.published:
            raise PublicationError("The model must first be published.")

        # set some values for use in examples when actual data hasn't been assigned
        if example == True:
            self.act = choice(ACS)
            self.vtb = random_dtstr()
            self.vte = random_dtstr()
            self.tr = random_dtstr()
            self.modified = random_dtstr()
            loc = get_latlon()
            self.latitude = str(loc[0])
            self.longitude = str(loc[1])

        indent = 2
        padding = ('').rjust(indent)
        xmlstr = ''
        if self.adapter:
            xmlstr += padding.rjust(indent) + '<s3m:ms-' + self.acuid + '>\n'
        xmlstr += padding.rjust(indent) + '<s3m:ms-' + self.mcuid + '>\n'
        xmlstr += padding.rjust(indent + 2) + '<label>' + self.label + '</label>\n'
        if self.cardinality['act'][0] > 0 or self.act is not None:
            xmlstr += padding.rjust(indent + 2) + '<act>' + self.act + '</act>\n'
        if self.cardinality['vtb'][0] > 0 or self.vtb is not None:
            xmlstr += padding.rjust(indent + 2) + '<vtb>' + self.vtb + '</vtb>\n'
        if self.cardinality['vte'][0] > 0 or self.vte is not None:
            xmlstr += padding.rjust(indent + 2) + '<vte>' + self.vte + '</vte>\n'
        if self.cardinality['tr'][0] > 0 or self.tr is not None:
            xmlstr += padding.rjust(indent + 2) + '<tr>' + self.tr + '</tr>\n'
        if self.cardinality['modified'][0] > 0 or self.modified is not None:
            xmlstr += padding.rjust(indent + 2) + '<modified>' + self.modified + '</modified>\n'
        if self.cardinality['location'][0] > 0 or self.latitude is not None or self.longitude is not None:
            xmlstr += padding.rjust(indent + 2) + '<latitude>' + self.latitude + '</latitude>\n'
            xmlstr += padding.rjust(indent + 2) + '<longitude>' + self.longitude + '</longitude>\n'

        return(xmlstr)

    def getJSONInstance(self, example=False):
        """
        Return an example JSON fragment for this model.
        """
        xml = self.getXMLInstance(example)
        parsed = xmltodict.parse(xml, encoding='UTF-8', process_namespaces=False)
        return(json.dumps(parsed, indent=2, sort_keys=False))


class XdIntervalType(XdAnyType):
    """
    Generic type defining an interval (i.e. range) of a comparable type.

    An interval is a contiguous subrange of a comparable base type.
    Used to define intervals of dates, times, quantities, etc. whose
    datatypes are the same and are ordered.

    In S3Model, they are primarily used in defining reference ranges.
    The datatype of upper and lower must be set in the model via the invltype
    attribute.
    """

    invlTypes = (int, Decimal, date, time, datetime, float)  # TODO: Add duration

    def __init__(self, label: str, invltype: str):
        super().__init__(label)
        self._xdtype = "XdIntervalType"

        self._lower = None
        self._upper = None
        self._lower_included = True
        self._upper_included = True
        self._lower_bounded = True
        self._upper_bounded = True
        self._interval_units = None
        self._units_id = None

        if invltype in XdIntervalType.invlTypes:
            self._interval_type = invltype
        else:
            raise ValueError("The Interval type must be one of; int, Decimal, date, time, datetime or float")

    @property
    def lower(self):
        """
        Defines the lower value of the interval.
        """
        return self._lower

    @lower.setter
    def lower(self, v):
        if not self.published:
            v = self._interval_type(v)
            if isinstance(v, self._interval_type):
                self._lower = v
            else:
                raise ValueError("The value couldn't be coerced to the Interval type. v = " + str(type(v)) + " interval_type = " + str(self._interval_type))
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def upper(self):
        """
        Defines the upper value of the interval.
        """
        return self._upper

    @upper.setter
    def upper(self, v):
        if not self.published:
            v = self._interval_type(v)
            if isinstance(v, self._interval_type):
                self._upper = v
            else:
                raise ValueError("The value couldn't be coerced to the Interval type. v = " + str(type(v)) + " interval_type = " + str(self._interval_type))
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def lower_included(self):
        """
        Is the lower value of the interval inclusive?
        Default is True.
        """
        return self._lower_included

    @lower_included.setter
    def lower_included(self, v):
        if not self.published:
            if isinstance(v, bool):
                self._lower_included = v
            else:
                raise ValueError("the lower_included value must be a Boolean.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def upper_included(self):
        """
        Is the upper value of the interval inclusive?
        Default is True.
        """
        return self._upper_included

    @upper_included.setter
    def upper_included(self, v):
        if not self.published:
            if isinstance(v, bool):
                self._upper_included = v
            else:
                raise ValueError("the upper_included value must be a Boolean.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def lower_bounded(self):
        """
        Is the lower value of the interval bounded?
        Default is True.
        """
        return self._lower_bounded

    @lower_bounded.setter
    def lower_bounded(self, v):
        if not self.published:
            if isinstance(v, bool):
                self._lower_bounded = v
            else:
                raise ValueError("the lower_bounded value must be a Boolean.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def upper_bounded(self):
        """
        Is the upper value of the interval bounded?
        Default is True.
        """
        return self._upper_bounded

    @upper_bounded.setter
    def upper_bounded(self, v):
        if not self.published:
            if isinstance(v, bool):
                self._upper_bounded = v
            else:
                raise ValueError("the upper_bounded value must be a Boolean.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def interval_units(self):
        """
        Defines the units for this Interval.

        A two member tuple consisting of the units name/abbreviation
        and a URI used as a definition.
        Example:
        ('kg', 'https://www.ema.europa.eu/documents/scientific-guideline/ich-m-5-ewg-units-measurements-controlled-vocabulary-step-5_en.pdf#0074')
        """
        return self._interval_units

    @interval_units.setter
    def interval_units(self, v):
        if not self.published:
            if isinstance(v, tuple):
                self._interval_units = v
            else:
                raise ValueError("the interval_units value must be a tuple.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not super(XdIntervalType, self).validate():
            return(False)
        else:
            return(True)

    def getModel(self):
        """
        Return a XML Schema complexType definition.
        """

        indent = 6
        padding = ('').rjust(indent)
        # Convert the bools to XSD strings
        li, ui, lb, ub = 'false', 'false', 'false', 'false'
        if self._lower_included:
            li = 'true'
        if self._upper_included:
            ui = 'true'
        if self._lower_bounded:
            lb = 'true'
        if self._upper_bounded:
            ub = 'true'
        type_transpose = {int:'int', Decimal:'decimal', float:'float'}
        xdstr = super().getModel()

        # XdInterval
        xdstr += padding.rjust(indent + 4) + ("<xs:element maxOccurs='1' minOccurs='0' name='lower' type='xs:" + type_transpose[self._interval_type] + "'/>\n")
        xdstr += padding.rjust(indent + 4) + ("<xs:element maxOccurs='1' minOccurs='0' name='upper' type='xs:" + type_transpose[self._interval_type] + "'/>\n")
        xdstr += padding.rjust(indent + 4) + ("<xs:element maxOccurs='1' minOccurs='1' name='lower-included' type='xs:boolean' fixed='" + li + "'/>\n")
        xdstr += padding.rjust(indent + 4) + ("<xs:element maxOccurs='1' minOccurs='1' name='upper-included' type='xs:boolean' fixed='" + ui + "'/>\n")
        xdstr += padding.rjust(indent + 4) + ("<xs:element maxOccurs='1' minOccurs='1' name='lower-bounded' type='xs:boolean' fixed='" + lb + "'/>\n")
        xdstr += padding.rjust(indent + 4) + ("<xs:element maxOccurs='1' minOccurs='1' name='upper-bounded' type='xs:boolean' fixed='" + ub + "'/>\n")

        if self._interval_units:
            self._units_id = cuid()
            xdstr += padding.rjust(indent + 4) + ("<xs:element maxOccurs='1' minOccurs='1' name='interval-units'  type='s3m:mc-" + self._units_id + "'/>\n")
        else:
            self._units_id = None

        xdstr += padding.rjust(indent + 4) + ("</xs:sequence>\n")
        xdstr += padding.rjust(indent + 4) + ("</xs:restriction>\n")
        xdstr += padding.rjust(indent + 2) + ("</xs:complexContent>\n")
        xdstr += padding.rjust(indent + 2) + ("</xs:complexType>\n\n")

        # interval units
        if self._units_id:
            xdstr += padding.rjust(indent + 2) + ("<xs:complexType name='mc-" + self._units_id + "'>\n")
            xdstr += padding.rjust(indent + 4) + ("<xs:complexContent>\n")
            xdstr += padding.rjust(indent + 6) + ("<xs:restriction base='s3m:InvlUnits'>\n")
            xdstr += padding.rjust(indent + 8) + ("<xs:sequence>\n")
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='1' name='units-name' type='xs:string' fixed='" + self._interval_units[0].strip() + "'/>\n")
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='1' name='units-uri' type='xs:anyURI' fixed='" + self._interval_units[1].strip() + "'/>\n")
            xdstr += padding.rjust(indent + 8) + ("</xs:sequence>\n")
            xdstr += padding.rjust(indent + 6) + ("</xs:restriction>\n")
            xdstr += padding.rjust(indent + 4) + ("</xs:complexContent>\n")
            xdstr += padding.rjust(indent + 2) + ("</xs:complexType>\n\n")
        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an example XML fragment for this model.
        """

        if not self.published:
            raise PublicationError("The model must first be published.")

        indent = 2
        padding = ('').rjust(indent)

        # Convert the bools to XSD strings
        li, ui, lb, ub = 'true', 'true', 'true', 'true'
        if not self.lower_included:
            li = 'false'
        if not self.upper_included:
            ui = 'false'
        if not self.lower_bounded:
            lb = 'false'
        if not self.upper_bounded:
            ub = 'false'

        xmlstr = super().getXMLInstance(example)
        if self.lower is not None:
            xmlstr += padding.rjust(indent + 2) + '<lower>' + str(self.lower).strip() + '</lower>\n'
        if self.upper is not None:
            xmlstr += padding.rjust(indent + 2) + '<upper>' + str(self.upper).strip() + '</upper>\n'
        xmlstr += padding.rjust(indent + 2) + '<lower-included>' + li + '</lower-included>\n'
        xmlstr += padding.rjust(indent + 2) + '<upper-included>' + ui + '</upper-included>\n'
        xmlstr += padding.rjust(indent + 2) + '<lower-bounded>' + lb + '</lower-bounded>\n'
        xmlstr += padding.rjust(indent + 2) + '<upper-bounded>' + ub + '</upper-bounded>\n'
        if self.interval_units is not None:
            xmlstr += padding.rjust(indent + 2) + '<interval-units>\n'
            xmlstr += padding.rjust(indent + 4) + '  <units-name>' + self.interval_units[0].strip() + '</units-name>\n'
            xmlstr += padding.rjust(indent + 4) + '  <units-uri>' + self.interval_units[1].strip() + '</units-uri>\n'
            xmlstr += padding.rjust(indent + 2) + '</interval-units>\n'
        xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.mcuid + '>\n'
        if self.adapter:
            xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.acuid + '>\n'

        return(xmlstr)


class ReferenceRangeType(XdAnyType):
    """
    Defines a named range to be associated with any ORDERED datum. Each such range is sensitive to the context,
    e.g. sex, age, location, and any other factor which affects ranges.
    May be used to represent high, low, normal, therapeutic, dangerous, critical, etc. ranges that are constrained by an interval.
    """

    def __init__(self, label):
        super().__init__(label)

        self._xdtype = "ReferenceRangeType"
        self._definition = ''
        self._interval = None
        self._is_normal = False

    @property
    def definition(self):
        """
        Term whose value indicates the meaning of this range, e.g. 'normal', 'critical', 'therapeutic' etc.
        """
        return self._definition

    @definition.setter
    def definition(self, v):
        if not self.published:
            if checkers.is_string(v):
                self._definition = v
            else:
                raise ValueError("the definition value must be a string.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def interval(self):
        """
        The data range for this reference range.
        """
        return self._interval

    @interval.setter
    def interval(self, v):
        if not self.published:
            if isinstance(v, XdIntervalType):
                self._interval = v
            else:
                raise ValueError("the interval value must be a XdIntervalType.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def is_normal(self):
        """
        True if this reference range defines values that are considered to be normal. In the context of the value in the definition element.
        """
        return self._is_normal

    @is_normal.setter
    def is_normal(self, v):
        if not self.published:
            if isinstance(v, bool):
                self._is_normal = v
            else:
                raise TypeError("the is_normal value must be a Boolean.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not super(ReferenceRangeType, self).validate():
            return(False)
        else:
            return(True)

    def getModel(self):
        """
        Return a XML Schema complexType definition.
        """
        indent = 6
        padding = ('').rjust(indent)
        normal = 'true' if self._is_normal else 'false'

        xdstr = super().getModel()
        # ReferenceRange
        xdstr += padding.rjust(indent + 4) + ("<xs:element maxOccurs='1' minOccurs='1' name='definition' type='xs:string' fixed='" + self.definition.strip() + "'/>\n")
        xdstr += padding.rjust(indent + 4) + ("<xs:element maxOccurs='1' minOccurs='1' name='interval' type='s3m:mc-" + self.interval.mcuid + "'/> \n")
        xdstr += padding.rjust(indent + 4) + ("<xs:element maxOccurs='1' minOccurs='1' name='is-normal' type='xs:boolean' fixed='" + str(self.is_normal).lower() + "'/>\n")
        xdstr += padding.rjust(indent + 4) + ("</xs:sequence>\n")
        xdstr += padding.rjust(indent + 4) + ("</xs:restriction>\n")
        xdstr += padding.rjust(indent + 4) + ("</xs:complexContent>\n")
        xdstr += padding.rjust(indent + 2) + ("</xs:complexType>\n\n")
        xdstr += self.interval.getModel()

        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an example XML fragment for this model.
        """
        if example:
            if not self.published:
                raise PublicationError("Cannot create an example unless the model is published.")
            # TODO: Create example

        # Convert the interval bools to XSD strings
        li, ui, lb, ub = 'true', 'true', 'true', 'true'
        if not self.interval.lower_included:
            li = 'false'
        if not self.interval.upper_included:
            ui = 'false'
        if not self.interval.lower_bounded:
            lb = 'false'
        if not self.interval.upper_bounded:
            ub = 'false'

        normal = 'true' if self._is_normal else 'false'

        indent = 6
        padding = ('').rjust(indent)
        xmlstr = super().getXMLInstance(example)

        xmlstr += padding.rjust(indent + 2) + '<definition>' + self.definition.strip() + '</definition>\n'
        xmlstr += padding.rjust(indent + 2) + '<interval>\n'
        xmlstr += padding.rjust(indent + 4) + '<label>' + self.interval.label + '</label>\n'
        if self.interval.lower is not None:
            xmlstr += padding.rjust(indent + 4) + '<lower>' + str(self.interval.lower).strip() + '</lower>\n'
        if self.interval.upper is not None:
            xmlstr += padding.rjust(indent + 4) + '<upper>' + str(self.interval.upper).strip() + '</upper>\n'
        xmlstr += padding.rjust(indent + 4) + '<lower-included>' + li + '</lower-included>\n'
        xmlstr += padding.rjust(indent + 4) + '<upper-included>' + ui + '</upper-included>\n'
        xmlstr += padding.rjust(indent + 4) + '<lower-bounded>' + lb + '</lower-bounded>\n'
        xmlstr += padding.rjust(indent + 4) + '<upper-bounded>' + ub + '</upper-bounded>\n'
        if self.interval.interval_units is not None:
            xmlstr += padding.rjust(indent + 4) + '<interval-units>\n'
            xmlstr += padding.rjust(indent + 6) + '<units-name>' + self.interval.interval_units[0].strip() + '</units-name>\n'
            xmlstr += padding.rjust(indent + 6) + '<units-uri>' + self.interval.interval_units[1].strip() + '</units-uri>\n'
            xmlstr += padding.rjust(indent + 4) + '</interval-units>\n'
        xmlstr += padding.rjust(indent + 2) + '</interval>\n'

        xmlstr += padding.rjust(indent + 2) + '<is-normal>' + normal + '</is-normal>\n'

        xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.mcuid + '>\n'
        if self.adapter:
            xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.acuid + '>\n'


        return(xmlstr)


class XdBooleanType(XdAnyType):
    """
    An enumerated type which represents boolean decisions such as true/false
    or yes/no answers.

    Useful where it is essential to devise the meanings (often questions in
    subjective data) carefully so that the only allowed result values result
    in one of the options; true or false but are presented to the user as
    a list of options.

    The possible choices for True or False are values in a dictionary.
    The class defines 'true_value' and 'false_value'.
    The instance implementation is restricted to only have a value for one of
    them based on the user choice from the options dictionary.

    The XdBooleanType should not be used as a replacement for enumerated choice
    types such as male/female, or similar choice sets.
    Such values should be modeled as XdStrings with enumerations and may reference
    a controlled vocabulary.
    In any case, the choice set often has more than two values.
    """

    def __init__(self, label: str, opt: dict):
        """
        Create an instance of a XdBooleanType.

        Parameters
        ----------
        label: str
            A human readable name lending semantics to the purpose of the model.
        opt: dictionary
            A dictionary where the two allowed keys are 'trues' and 'falses'.
            The items associated with these keys are a list of options for the user to
            choose from.
        """
        super().__init__(label)
        self._true_value = None
        self._false_value = None
        self._xdtype = "XdBooleanType"
        self._options = None

        if isinstance(opt, dict) and list(opt.keys()) == ['trues', 'falses']:
            if isinstance(opt['trues'], list) and isinstance(opt['falses'], list):
                self._options = opt
            else:
                raise TypeError("The values of 'trues' and 'falses' must be a list of strings.")
        else:
            raise ValueError("The the options value must be a dictionary with two keys; 'trues' and 'falses'. Their items must be a list of strings.")

    @property
    def true_value(self):
        """
        A string that represents a boolean True in the implementation.
        These are constrained by a set of enumerations.
        """
        return self._true_value

    @true_value.setter
    def true_value(self, v):
        if self.published:
            if v == None:
                self._true_value = None
            elif v in self._options['trues'] and self._false_value == None:
                self._true_value = v
            else:
                raise ValueError("the true_value value must be in the options['trues'] list and the false_value must be None.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def false_value(self):
        """
        A string that represents a boolean False in the implementation.
        These are constrained by a set of enumerations.
        """
        return self._false_value

    @false_value.setter
    def false_value(self, v):
        if self.published:
            if v == None:
                self._false_value = None
            elif v in self._options['falses'] and self._true_value == None:
                self._false_value = v
            else:
                raise ValueError("the false_value value must be in the options['falses'] list and the true_value must be None.")
        else:
            raise PublicationError("The model has not been published.")

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not super(XdBooleanType, self).validate():
            return(False)
        elif self._options == None:
            raise ValidationError("Missing options dictionary.")
        elif not isinstance(self._options, dict) or not list(self._options.keys()) == ['trues', 'falses']:
            raise ValidationError("The options dictionary keys are invalid.")
        elif not isinstance(self._options['trues'], list) or not isinstance(self._options['falses'], list):
            raise ValidationError("The options dictionary values must be a list.")
        elif self.true_value is not None and self.false_value is not None:
            raise ValidationError("Either the true_value or the false_value must be None.")
        else:
            return(True)

    def getModel(self):
        """
        Return a XML Schema complexType definition.
        """
        if not super(XdBooleanType, self).validate():
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + " failed validation.")

        xdstr = super().getModel()

        trues = self._options['trues']
        falses = self._options['falses']
        indent = 2
        padding = ('').rjust(indent)
        # XdBooleanType
        xdstr += padding.rjust(indent + 8) + ("<xs:choice maxOccurs='1' minOccurs='1'>\n")
        xdstr += padding.rjust(indent + 8) + ("<xs:element name='true-value'>\n")
        xdstr += padding.rjust(indent + 10) + ("<xs:simpleType>\n")
        xdstr += padding.rjust(indent + 12) + ("<xs:restriction base='xs:string'>\n")
        for n in range(len(trues)):
            xdstr += padding.rjust(indent + 16) + ("<xs:enumeration value='" + trues[n].strip() + "'/>\n")
        xdstr += padding.rjust(indent + 12) + ("</xs:restriction>\n")
        xdstr += padding.rjust(indent + 10) + ("</xs:simpleType>\n")
        xdstr += padding.rjust(indent + 8) + ("</xs:element>\n")
        xdstr += padding.rjust(indent + 8) + ("<xs:element name='false-value'>\n")
        xdstr += padding.rjust(indent + 10) + ("<xs:simpleType>\n")
        xdstr += padding.rjust(indent + 12) + ("<xs:restriction base='xs:string'>\n")
        for n in range(len(falses)):
            xdstr += padding.rjust(indent + 16) + ("<xs:enumeration value='" + falses[n].strip() + "'/>\n")
        xdstr += padding.rjust(indent + 12) + ("</xs:restriction>\n")
        xdstr += padding.rjust(indent + 10) + ("</xs:simpleType>\n")
        xdstr += padding.rjust(indent + 8) + ("</xs:element>\n")

        xdstr += padding.rjust(indent + 8) + ("</xs:choice>\n")

        xdstr += padding.rjust(indent + 6) + '</xs:sequence>\n'
        xdstr += padding.rjust(indent + 4) + '</xs:restriction>\n'
        xdstr += padding.rjust(indent + 2) + '</xs:complexContent>\n'
        xdstr += padding.rjust(indent) + '</xs:complexType>\n'

        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an XML fragment for this model.
        """
        if example:
            if not self.published:
                raise PublicationError("Cannot create an example unless the model is published.")
            # randomly choose an option
            tf = choice(list(self._options.keys()))
            if tf == 'trues':
                self.true_value = choice(self._options[tf])
            elif tf == 'falses':
                self.false_value = choice(self._options[tf])
            else:
                raise ValueError("Something bad happened selecting an example value.")

        indent = 2
        padding = ('').rjust(indent)
        xmlstr = super().getXMLInstance(example)

        if self.true_value is not None:
            xmlstr += padding.rjust(indent + 2) + '<true-value>' + self.true_value + '</true-value>\n'
        elif self.false_value is not None:
            xmlstr += padding.rjust(indent + 2) + '<false-value>' + self.false_value + '</false-value>\n'
        else:
            xmlstr += padding.rjust(indent + 2) + '<!-- ** Missing required instance data. ** -->\n'

        xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.mcuid + '>\n'
        if self.adapter:
            xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.acuid + '>\n'


        return(xmlstr)


class XdLinkType(XdAnyType):
    """
    Used to specify a Universal Resource Identifier. Set the pattern facet to accommodate your needs in the DM.
    Primary intended use is to provide a mechanism that can be used to link together S3M Data Models. Can also
    be used to link to other resources.

    The relation element requires the use of a descriptive term for the link with an optional URI pointing to the
    source vocabulary.

    In most usecases the modeler will define all three of these using the 'fixed' attribute.
    Other usecases will have the 'relation' and 'relation-uri' elements fixed and the application will provide the
    'link'.
    """

    def __init__(self, label: str):
        """
        The semantic label (name of the model) is required.
        """
        super().__init__(label)
        self._xdtype = "XdLinkType"
        self._fixed = False
        self._link = ''
        self._relation = None
        self._relation_uri = None
        self.cardinality = ('relation_uri', [0, 1])
        self.cardinality = ('link', [0, 1])

    @property
    def fixed(self):
        """
        The modeler determines if this is a fixed pointer and has included the
        hardcoded 'link' if it is fixed. In case fo a fixed pointer it must
        be provided after the 'fixed' attribute is set True and before
        'published' is set to True.
        """
        return self._fixed

    @fixed.setter
    def fixed(self, v):
        if not self.published:
            if isinstance(v, bool):
                self._fixed = v
            else:
                raise TypeError("the fixed value must be a boolean.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def link(self):
        """
        A required URI. A URL to another Data Model or just the dm-{uuid}.
        """
        return self._link

    @link.setter
    def link(self, v):
        if checkers.is_string(v):
            if self.published and not self.fixed:
                self._link = v
            elif not self.published and self.fixed:
                self._link = v
            else:
                raise ValueError("Cannot add the link. Published: " + str(self.published) + " Fixed: " + str(self.fixed))
        else:
            raise TypeError("the link value must be a string.")

    @property
    def relation(self):
        """
        A required term, normally drawn from a vocabulary or ontology such as the rdf:label of OBO RO.
        """
        return self._relation

    @relation.setter
    def relation(self, v):
        if not self.published:
            if checkers.is_string(v):
                self._relation = v
            else:
                raise TypeError("the relation value must be a string.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def relation_uri(self):
        """
        A URI where the definition of the relation element term can be found.
        Normally points to an ontology such as the OBO RO http://purl.obolibrary.org/obo/ro.owl
        """
        return self._relation_uri

    @relation_uri.setter
    def relation_uri(self, v):
        if not self.published:
            if checkers.is_url(v):
                self._relation_uri = v
            else:
                raise TypeError("the relation_uri value must be a URL.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not super(XdLinkType, self).validate():
            return(False)
        elif self.cardinality['relation_uri'][0] not in [0, 1] or self.cardinality['relation_uri'][1] not in [0, 1]:
            raise ValidationError("The cardinality of relation_uri is invalid: " + str(self.cardinality['relation_uri']))
        else:
            return(True)

    def getModel(self):
        """
        Return a XML Schema complexType definition.
        """
        self.validate()
        indent = 2
        padding = ('').rjust(indent)

        xdstr = super().getModel()
        # XdLinkType
        if not self.fixed:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['link'][0]) + "' name='link' type='xs:anyURI'/>\n")
        else:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='1' name='link' type='xs:anyURI' fixed='" + escape(self.link.strip()) + "'/>\n")
        if not self.relation:
            raise ValueError("You must add a relationship.")
        else:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='1' name='relation' type='xs:string' fixed='" + escape(self.relation.strip()) + "'/>\n")
        if not self.relation_uri:
            raise ValueError("You must add a URI for the relationship location.")
        else:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['relation_uri'][0]) + "' name='relation-uri' type='xs:anyURI' fixed='" + escape(self.relation_uri.strip()) + "'/>\n")
        xdstr += padding.rjust(indent + 6) + '</xs:sequence>\n'
        xdstr += padding.rjust(indent + 4) + '</xs:restriction>\n'
        xdstr += padding.rjust(indent + 2) + '</xs:complexContent>\n'
        xdstr += padding.rjust(indent) + '</xs:complexType>\n'

        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an example XML fragment for this model.
        """
        if example == True:
            if not self.published:
                raise PublicationError("Cannot create an example unless the model is published.")
            self.link = 'https://s3model.com/dmlib/dm-cjmuxu61q0000z98p91fewlhm'
            self.relation = 'Related Data Model'
            self.relation_uri = 'https://s3model.com/examples/related'

        indent = 2
        padding = ('').rjust(indent)
        xmlstr = super().getXMLInstance(example)

        xmlstr += padding.rjust(indent + 2) + '<link>' + self.link + '</link>\n'
        xmlstr += padding.rjust(indent + 2) + '<relation>' + self.relation + '</relation>\n'
        xmlstr += padding.rjust(indent + 2) + '<relation-uri>' + self.relation_uri + '</relation-uri>\n'

        xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.mcuid + '>\n'
        if self.adapter:
            xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.acuid + '>\n'

        return(xmlstr)


class XdStringType(XdAnyType):
    """
    The string data type can contain characters, line feeds, carriage returns, and tab characters.
    The use cases are for any free form text entry or for any enumerated lists.
    Additionally the minimum and maximum lengths may be set and regular expression patterns may be specified.
    """

    def __init__(self, label):
        """
        The semantic label (name of the model) is required.
        """
        super().__init__(label)
        self._xdtype = "XdStringType"

        self._value = None
        self._language = None
        self._enums = []
        self._regex = None
        self._default = None
        self._length = None
        self.cardinality = ('value', [0, 1])
        self.cardinality = ('language', [0, 1])

    @property
    def value(self):
        """
        The string value of the item.
        """
        return self._value

    @value.setter
    def value(self, v):
        if self.published:
            if checkers.is_string(v):
                self._value = v
            else:
                raise TypeError("the value must be a string.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def language(self):
        """
        Optional indicator of the localised language in which this data-type is written.
        Only required when the language used here is different from the enclosing Data Model.
        """
        return self._language

    @language.setter
    def language(self, v):
        if self.published:
            if checkers.is_string(v):
                self._language = v
            else:
                raise TypeError("the language value must be a string.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def length(self):
        """
        The length constraints on the xdstring_value.
        The value can be an integer which will set the exact length constraint or it can be a tuple of the min/max length pair.
        The values inside the tuple can be integers or the None value wich will cause the min or max value to not be set.
        """
        return self._length

    @length.setter
    def length(self, v):
        if not self.published:
            if v == None:
                self._length = v
            else:
                if len(self._enums) > 0 or self.regex is not None:
                    raise ValueError("The elements 'length', 'enums' and 'regex' are mutally exclusive.  Set length and regex to 'None' or enums to '[]'.")
                if checkers.is_integer(v) and v >= 1:
                    self._length = v
                elif isinstance(v, tuple) and len(v) == 2:
                    if not isinstance(v[0], (int, None)) or not isinstance(v[1], (int, None)):
                        raise TypeError("The tuple must contain two values of either type, None or integers.")
                    elif isinstance(v[0], int) and isinstance(v[1], int) and v[0] > v[1]:
                        raise ValueError("Minimum length must be smaller or equal to maximum length.")
                    self._length = v
                else:
                    raise TypeError("The length value must be an integer (exact length) or a tuple (min/max lengths).")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def regex(self):
        """
        A regular expression to constrain the string value. The regualr expression must meet the constraints for XML Schema.
        See: https://www.regular-expressions.info/xml.html
        """
        return self._regex

    @regex.setter
    def regex(self, v):
        if not self.published:
            if v == None:
                self._regex = v
            elif checkers.is_string(v):
                if len(self._enums) > 0 or self.length is not None:
                    raise ValueError("The elements 'length', 'enums' and 'regex' are mutally exclusive.  Set length and regex to 'None' or enums to '[]'.")
                try:
                    re.compile(v)
                    self._regex = v
                except re.error:
                    raise ValueError("The value is not a valid regular expression.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def enums(self):
        """
        A list of two member tuples (enumeration, URI semantics for the enumeration).

        The enumerations are string values used to constrain the value of the item.
        The URI semantics for the enumeration provides a definition (preferable a URL) for the enumeration.
        Example: ('Blue','http://www.color-wheel-pro.com/color-meaning.html#Blue')
        """
        return self._enums

    @enums.setter
    def enums(self, v):
        if not self.published:
            if v == []:
                self._enums = v

            if self.regex is not None or self.length is not None:
                raise ValueError("The elements 'length', enums' and 'regex' are mutally exclusive. Set length and regex to 'None' or enums to '[]'.")

            if isinstance(v, list):
                for enum in v:
                    if not isinstance(enum, tuple):
                        raise TypeError("The enumerations and definitions must be strings.")

                    if not isinstance(enum[0], str) or not isinstance(enum[1], str):
                        raise TypeError("The enumerations and definitions must be strings.")

                self._enums = v
            else:
                raise TypeError("The enumerations must be a list of tuples.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def default(self):
        """
        The default value for the string value of the item.
        """
        return self._default

    @default.setter
    def default(self, v):
        if not self.published:
            if v == None:
                self._length = v
            elif checkers.is_string(v):
                self._default = v
            else:
                raise TypeError("The default value must be a string or None.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not super(XdStringType, self).validate():
            return(False)
        else:
            return(True)


    def getModel(self):
        """
        Return a XML Schema complexType definition.
        """
        if not super(XdStringType, self).validate():
            raise ValidationError(self.__class__.__name__ + ' : ' + self.label + " failed validation.")

        indent = 2
        padding = ('').rjust(indent)

        xdstr = super().getModel()
        # XdStringType
        if isinstance(self.regex, str):
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['value'][0]) + "' name='xdstring-value'>\n")
            xdstr += padding.rjust(indent + 12) + ("<xs:simpleType>\n")
            xdstr += padding.rjust(indent + 14) + ("<xs:restriction base='xs:string'>\n")
            xdstr += padding.rjust(indent + 16) + ("<xs:pattern value='" + self.regex.strip() + "'/>\n")
            xdstr += padding.rjust(indent + 14) + ("</xs:restriction>\n")
            xdstr += padding.rjust(indent + 12) + ("</xs:simpleType>\n")
            xdstr += padding.rjust(indent + 10) + ("</xs:element>\n")
        if self.length is not None:
            if isinstance(self.length, int):
                xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['value'][0]) + "' name='xdstring-value'>\n")
                xdstr += padding.rjust(indent + 10) + ("<xs:simpleType>\n")
                xdstr += padding.rjust(indent + 12) + ("<xs:restriction base='xs:string'>\n")
                xdstr += padding.rjust(indent + 14) + ("<xs:length value='" + str(self.length).strip() + "'/>\n")
                xdstr += padding.rjust(indent + 12) + ("</xs:restriction>\n")
                xdstr += padding.rjust(indent + 10) + ("</xs:simpleType>\n")
                xdstr += padding.rjust(indent + 8) + ("</xs:element>\n")
            elif (self.length, tuple) and len(self.length) == 2:
                xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['value'][0]) + "' name='xdstring-value'>\n")
                xdstr += padding.rjust(indent + 12) + ("<xs:simpleType>\n")
                xdstr += padding.rjust(indent + 14) + ("<xs:restriction base='xs:string'>\n")
                if isinstance(self.length[0], int):
                    xdstr += padding.rjust(indent + 16) + ("<xs:minLength value='" + str(self.length[0]).strip() + "'/>\n")
                if isinstance(self.length[1], int):
                    xdstr += padding.rjust(indent + 16) + ("<xs:maxLength value='" + str(self.length[1]).strip() + "'/>\n")
                xdstr += padding.rjust(indent + 14) + ("</xs:restriction>\n")
                xdstr += padding.rjust(indent + 12) + ("</xs:simpleType>\n")
                xdstr += padding.rjust(indent + 10) + ("</xs:element>\n")
        elif self.default is not None and self.regex is None and self.length is None:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['value'][0]) + "' name='xdstring-value' type='xs:string' default='" + escape(self.default) + "'/>\n")
        elif self.default is None and self.regex is None and self.length is None and len(self.enums) == 0:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['value'][0]) + "' name='xdstring-value' type='xs:string'/>\n")
        else:
            pass

        # Process Enumerations
        if len(self.enums) > 0:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['value'][0]) + "' name='xdstring-value'>\n")
            xdstr += padding.rjust(indent + 12) + ("<xs:simpleType>\n")
            xdstr += padding.rjust(indent + 14) + ("<xs:restriction base='xs:string'>\n")
            for n in range(len(self.enums)):
                xdstr += padding.rjust(indent + 16) + ("<xs:enumeration value='" + escape(self.enums[n][0].strip()) + "'>\n")
                xdstr += padding.rjust(indent + 16) + ("<xs:annotation>\n")
                xdstr += padding.rjust(indent + 18) + ("<xs:appinfo>\n")
                xdstr += padding.rjust(indent + 20) + ("<rdfs:Class rdf:about='mc-" + self.mcuid + "/xdstring-value/" + quote(self.enums[n][0].strip()) + "'>\n")
                xdstr += padding.rjust(indent + 20) + ("  <rdfs:subPropertyOf rdf:resource='mc-" + self.mcuid + "'/>\n")
                xdstr += padding.rjust(indent + 20) + ("  <rdfs:label>" + self.enums[n][0].strip() + "</rdfs:label>\n")
                xdstr += padding.rjust(indent + 20) + ("  <rdfs:isDefinedBy>" + self.enums[n][1].strip() + "</rdfs:isDefinedBy>\n")
                xdstr += padding.rjust(indent + 20) + ("</rdfs:Class>\n")
                xdstr += padding.rjust(indent + 18) + ("</xs:appinfo>\n")
                xdstr += padding.rjust(indent + 16) + ("</xs:annotation>\n")
                xdstr += padding.rjust(indent + 16) + ("</xs:enumeration>\n")
            xdstr += padding.rjust(indent + 14) + ("</xs:restriction>\n")
            xdstr += padding.rjust(indent + 12) + ("</xs:simpleType>\n")
            xdstr += padding.rjust(indent + 10) + ("</xs:element>\n")

        if self.language is not None and isinstance(self.language, str):
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['language'][0]) + "' name='xdstring-language' type='xs:language' default='" + self.language + "'/>\n")

        xdstr += padding.rjust(indent + 6) + '</xs:sequence>\n'
        xdstr += padding.rjust(indent + 4) + '</xs:restriction>\n'
        xdstr += padding.rjust(indent + 2) + '</xs:complexContent>\n'
        xdstr += padding.rjust(indent) + '</xs:complexType>\n'

        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an example XML fragment for this model.
        """

        if self.value == None and example == True:
            if not self.published:
                raise PublicationError("Cannot create an example unless the model is published.")
            if len(self.enums) > 0:
                print("Has enums")
                if self.default is not None:
                    self.value = self.default
                else:
                    self.value = choice(self.enums)[0]
            elif isinstance(self.length, int):
                self.value = 'w' * self.length
            elif isinstance(self.length, tuple):
                self.value = 'd' * self.length[0]  # insure to meet the minimum
            elif self.default is not None:
                self.value = self.default
            elif self.regex is not None:
                try:
                    self.value = exrex.getone(self.regex)
                except:
                    self.value = "Could not generate a valid example for the regex."
            else:
                self.value = 'Generated Default String'  # just a default when no other option applies

        indent = 2
        padding = ('').rjust(indent)
        xmlstr = super().getXMLInstance(example)
        if self.value == None:
            self.value = 'A Default String'
        xmlstr += padding.rjust(indent + 2) + '<xdstring-value>' + self.value + '</xdstring-value>\n'
        if self.language is not None:
            xmlstr += padding.rjust(indent + 2) + '<xdstring-language>' + self.language + '</xdstring-language>\n'

        xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.mcuid + '>\n'
        if self.adapter:
            xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.acuid + '>\n'


        return(xmlstr)


class XdFileType(XdAnyType):
    """
    A type to use for encapsulated content (aka. files) for image, audio and
    other media types with a defined MIME type.

    This type provides a choice of embedding the content into the data or using
    a URL to point to the content.
    """

    def __init__(self, label: str):
        """
        The semantic label (name of the model) is required.
        """
        super().__init__(label)
        self._xdtype = "XdFileType"

        self._size = None
        self._encoding = None
        self._language = None
        self._formalism = None
        self._media_type = None
        self._compression_type = None
        self._hash_result = None
        self._hash_function = None
        self._alt_txt = None
        # choice of uri or media_content
        self._uri = None
        self._media_content = None
        self._content_type = 'uri'

        self.cardinality = ('size', [0, 1])
        self.cardinality = ('encoding', [0, 1])
        self.cardinality = ('language', [0, 1])
        self.cardinality = ('formalism', [0, 1])
        self.cardinality = ('media_type', [0, 1])
        self.cardinality = ('compression_type', [0, 1])
        self.cardinality = ('hash_result', [0, 1])
        self.cardinality = ('hash_function', [0, 1])
        self.cardinality = ('alt_txt', [0, 1])

    @property
    def content_type(self):
        """
        The content_type determines if the model will require a URI pointer to
        the content or if it will be base64Binary encoded and embedded in the
        data instance. The valid values are 'uri' or 'embed'. Default is 'uri'.
        """
        return self._content_type

    @content_type.setter
    def content_type(self, v: str):
        if not self.published:
            if v.lower() in ('uri', 'embed'):
                self._content_type = v.lower()
            else:
                raise TypError("The content_type value must be an a string and one of 'uri' or 'embed'.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def size(self):
        """
        Original size in bytes of unencoded encapsulated data. I.e. encodings
        such as base64, hexadecimal, etc.
        """
        return self._size

    @size.setter
    def size(self, v):
        if self.published:
            if checkers.is_integer(v):
                self._size = v
            else:
                raise TypeError("The size value must be an integer.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def encoding(self):
        """
        Name of character encoding scheme in which this value is encoded.

        Coded from the IANA charcater set table:
        http://www.iana.org/assignments/character-sets

        Unicode is the default assumption in S3Model, with UTF-8 being the
        assumed encoding.
        This optional element allows for variations from these assumptions.
        """
        return self._encoding

    @encoding.setter
    def encoding(self, v):
        if self.published:
            if checkers.is_string(v):
                self._encoding = v
            else:
                raise TypeError("the encoding value must be a string.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def language(self):
        """
        Optional indicator of the localised language of the content.

        Typically remains optional in the CMC and used at runtime when the
        content is in a different language from the enclosing CMC.
        """
        return self._language

    @language.setter
    def language(self, v):
        if self.published:
            if checkers.is_string(v):
                self._language = v
            else:
                raise TypeError("the language value must be a string.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def formalism(self):
        """
        Name of the formalism or syntax used to inform an application regarding
        a candidate parser to use on the content.

        Examples might include: 'ATL', 'MOLA', 'QVT', 'GDL', 'GLIF', 'XML', etc.
        """
        return self._formalism

    @formalism.setter
    def formalism(self, v):
        if self.published:
            if checkers.is_string(v):
                self._formalism = v
            else:
                raise TypeError("the formalism value must be a string.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def media_type(self):
        """
        Media (MIME) type of the original media-content w/o any compression.

        See IANA registered types:
        http://www.iana.org/assignments/media-types/media-types.xhtml
        """
        return self._media_type

    @media_type.setter
    def media_type(self, v):
        if self.published:
            if checkers.is_string(v):
                self._media_type = v
            else:
                raise TypeError("the media_type value must be a string.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def compression_type(self):
        """
        Compression/archiving mime-type.

        If this elements does not exist then it means there is no
        compression/archiving.

        For a list of common mime-types for compression/archiving see:
        http://en.wikipedia.org/wiki/List_of_archive_formats.
        """
        return self._compression_type

    @compression_type.setter
    def compression_type(self, v):
        if self.published:
            if checkers.is_string(v):
                self._compression_type = v
            else:
                raise TypeError("the compression_type value must be a string.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def hash_result(self):
        """
        Hash function result of the 'media-content'.

        There must be a corresponding hash function type listed for this
        to have any meaning.

        See: http://en.wikipedia.org/wiki/List_of_hash_functions#Cryptographic_hash_functions
        """
        return self._hash_result

    @hash_result.setter
    def hash_result(self, v):
        if self.published:
            if checkers.is_string(v):
                self._hash_result = v
            else:
                raise TypeError("the hash_result value must be a string.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def hash_function(self):
        """
        Hash function used to compute hash-result.

        See: http://en.wikipedia.org/wiki/List_of_hash_functions#Cryptographic_hash_functions
        """
        return self._hash_function

    @hash_function.setter
    def hash_function(self, v):
        if self.published:
            if checkers.is_string(v):
                self._hash_function = v
            else:
                raise TypeError("the hash_function value must be a string.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def alt_txt(self):
        """
        Text to display in lieu of multimedia display or execution.
        """
        return self._alt_txt

    @alt_txt.setter
    def alt_txt(self, v):
        if self.published:
            if checkers.is_string(v):
                self._alt_txt = v
            else:
                raise TypeError("the alt_txt value must be a string.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def uri(self):
        """
        URI reference to electronic information stored outside the record
        as a file, database entry etc.; if supplied as a reference.
        """
        return self._uri

    @uri.setter
    def uri(self, v):
        if self.published:
            if v == None:
                self._uri = v
            elif self._media_content == None and isinstance(v, (str)):
                self._uri = v
            else:
                raise TypeError("the uri value must be a URL and media_content must be None.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def media_content(self):
        """
        The content, if stored locally.

        The modeler chooses either a uri or local content element.
        If the passed value is a string it will be converted to bytes and
        base64 encoded.

        If it is already bytes then it is just encoded.
        """
        return self._media_content

    @media_content.setter
    def media_content(self, v):
        if self.published:
            if self._uri == None:
                if isinstance(v, (bytes, type(None))):
                    self._media_content = v
                else:
                    raise ValueError("the media_content value must be a bytes object that is Base64 encoded.")
            else:
                raise TypeError("uri must be None to assign media_content.")
        else:
            raise PublicationError("The model has not been published.")

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not super(XdFileType, self).validate():
            return(False)
        else:
            return(True)

    def getModel(self):
        """
        Return a XML Schema complexType definition.
        """
        self.validate()
        indent = 2
        padding = ('').rjust(indent)

        xdstr = super().getModel()
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['size'][0]) + '" name="size" type="xs:int"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['encoding'][0]) + '" name="encoding" type="xs:string"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['language'][0]) + '" name="xdfile-language" type="xs:language"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['formalism'][0]) + '" name="formalism" type="xs:string"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['media_type'][0]) + '" name="media-type" type="xs:string"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['compression_type'][0]) + '" name="compression-type" type="xs:string"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['hash_result'][0]) + '" name="hash-result" type="xs:string"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['hash_function'][0]) + '" name="hash-function" type="xs:string"/>\n'
        xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="' + str(self.cardinality['alt_txt'][0]) + '" name="alt-txt" type="xs:string"/>\n'

        if self.content_type == 'uri':
            xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="1" name="uri" type="xs:anyURI"/>\n'
        elif self.content_type == 'embed':
            xdstr += padding.rjust(indent + 8) + '<xs:element maxOccurs="1" minOccurs="1" name="media-content" type="xs:base64Binary"/>\n'
        else:
            raise ValueError("The content_type for the model must be specified as 'uri' or 'embed'.")

        xdstr += padding.rjust(indent + 6) + '</xs:sequence>\n'
        xdstr += padding.rjust(indent + 4) + '</xs:restriction>\n'
        xdstr += padding.rjust(indent + 2) + '</xs:complexContent>\n'
        xdstr += padding.rjust(indent) + '</xs:complexType>\n\n'

        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an example XML fragment for this model.
        """

        if example == True:
            if not self.published:
                raise PublicationError("Cannot create an example unless the model is published.")
            self.size = randint(1, 1000000000)
            self.encoding = 'UTF-8'
            self.language = 'en-US'
            self.formalism = 'ADL'
            self.media_type = 'text/example'
            self.compression_type = 'tar.gz'
            self.hash_result = '8c11e544038c03a86d4da378199cf897'
            self.hash_function = 'MD5'
            self.alt_txt = 'Example file model'
            self.uri = 'https://www.s3model.com/ns/s3m/s3model_3_1_0.xsd'

        indent = 2
        padding = ('').rjust(indent)
        xmlstr = super().getXMLInstance(example)
        if self.size is not None:
            xmlstr += padding.rjust(indent + 2) + '<size>' + str(self.size) + '</size>\n'
        if self.encoding is not None:
            xmlstr += padding.rjust(indent + 2) + '<encoding>' + self.encoding.strip() + '</encoding>\n'
        if self.language is not None:
            xmlstr += padding.rjust(indent + 2) + '<xdfile-language>' + self.language.strip() + '</xdfile-language>\n'
        if self.formalism is not None:
            xmlstr += padding.rjust(indent + 2) + '<formalism>' + self.formalism.strip() + '</formalism>\n'
        if self.media_type is not None:
            xmlstr += padding.rjust(indent + 2) + '<media-type>' + self.media_type.strip() + '</media-type>\n'
        if self.compression_type is not None:
            xmlstr += padding.rjust(indent + 2) + '<compression-type>' + self.compression_type.strip() + '</compression-type>\n'
        if self.hash_result is not None:
            xmlstr += padding.rjust(indent + 2) + '<hash-result>' + self.hash_result.strip() + '</hash-result>\n'
        if self.hash_function is not None:
            xmlstr += padding.rjust(indent + 2) + '<hash-function>' + self.hash_function.strip() + '</hash-function>\n'
        if self.alt_txt is not None:
            xmlstr += padding.rjust(indent + 2) + '<alt-txt>' + self.alt_txt.strip() + '</alt-txt>\n'
        if self.uri is not None:
            xmlstr += padding.rjust(indent + 2) + '<uri>' + self.uri.strip() + '</uri>\n'
        elif self.media_content is not None:
            xmlstr += padding.rjust(indent + 2) + '<media-content>' + str(self.media_content) + '</media-content>\n'

        xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.mcuid + '>\n'
        if self.adapter:
            xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.acuid + '>\n'

        return(xmlstr)


class XdOrderedType(XdAnyType):
    """
    Serves as an abstract common ancestor of all ordered types
    """
    @abstractmethod
    def __init__(self, label):
        super().__init__(label)

        self._referenceranges = []
        self._normal_status = None
        self.cardinality = ('referencerange', [0, None])
        self.cardinality = ('normal_status', [0, 1])

    @property
    def referenceranges(self):
        """
        Optional list of ReferenceRanges for this value in its
        particular measurement context.
        """
        return self._referenceranges

    @referenceranges.setter
    def referenceranges(self, v):
        if not self.published:
            if not checkers.is_type(v, "ReferenceRangeType"):
                raise TypeError("The referencerange value must be a ReferenceRangeType.")
            self.referenceranges.append(v)
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def normal_status(self):
        """
        Optional normal status indicator of value with respect to normal range
        for this value.

        Often used in situations such as medical lab results when coded by
        ordinals in series such as; HHH, HH, H, (nothing), L, LL, LLL, etc.
        """
        return self._normal_status

    @normal_status.setter
    def normal_status(self, v):
        if self.published:
            if checkers.is_string(v):
                self._normal_status = v
            else:
                raise TypeError("the normal_status value must be a string.")
        else:
            raise PublicationError("The model has not been published.")

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not super(XdOrderedType, self).validate():
            return(False)
        else:
            return(True)

    def getModel(self):
        """
        Return a XML Schema complexType definition.
        """
        self.validate()
        indent = 4
        padding = ('').rjust(indent)

        xdstr = super().getModel()
        # XdOrdered
        if len(self.referenceranges) > 0:
            for rr in self.referenceranges:
                xdstr += padding.rjust(indent + 6) + "<xs:element maxOccurs='1' minOccurs='1' ref='s3m:ms-" + rr.mcuid + "'/> \n"
        if self.normal_status is not None:
            xdstr += padding.rjust(indent + 6) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['normal_status'][0]) + "' name='normal-status' type='xs:string' fixed='" + escape(self.normal_status.strip()) + "'/> \n")
        else:
            xdstr += padding.rjust(indent + 6) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['normal_status'][0]) + "' name='normal-status' type='xs:string'/> \n")

        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an example XML fragment for this model.
        """
        if example == True:
            self._referenceranges = [] # TODO: Build a reference range
            self.normal_status = 'normal'

        indent = 4
        padding = ('').rjust(indent)
        xmlstr = super().getXMLInstance(example)
        if len(self.referenceranges) > 0:
            for rr in self.referenceranges:
                xmlstr += rr.getXMLInstance()
        if self.normal_status is not None:
            xmlstr += padding.rjust(indent) + '<normal-status>' + self.normal_status + '</normal-status>\n'

        return(xmlstr)


class XdOrdinalType(XdOrderedType):
    """
    Models rankings and scores, e.g., pain, Apgar values, educational level,
    and the Likert Scale where there is;

    * implied ordering,
    * no implication that the distance between each value is constant, and
    * the total number of values is finite.

    Note that the term ‘ordinal’ in mathematics means natural numbers only.
    In this case, any decimal is allowed since negative, and zero values are
    used by medical and other professionals for centering values around a
    neutral point. Also, decimal values are sometimes used such as 0.5 or .25

        Examples of sets of ordinal values are;

        * -3, -2, -1, 0, 1, 2, 3 -- reflex response values
        * 0, 1, 2 -- Apgar values

        Also used for recording any clinical or other data which is customarily
        recorded using symbolic values. Examples;

        * the results on a urinalysis strip, e.g. {neg, trace, +, ++, +++} are
          used for leukocytes, protein, nitrites etc;
        * for non-haemolysed blood {neg, trace, moderate};
        * for haemolysed blood {neg, trace, small, moderate, large}.

    If a normal status is set it should be a member of the set of symbols.
    """

    def __init__(self, label: str, choices):
        """
        The semantic label (name of the model) and the
        choices list are required.
        """
        super().__init__(label)
        self._xdtype = "XdOrdinalType"

        self._ordinal = None
        self._symbol = None
        self._choices = choices

    @property
    def ordinal(self):
        """
        Value in ordered enumeration of values.

        The base decimal is zero with any number of decimal values used to order the symbols.
        Example 1: 0 = Trace, 1 = +, 2 = ++, 3 = +++, etc. Example 2: 0 = Mild, 1 = Moderate, 2 = Severe
        """
        return self._ordinal

    @ordinal.setter
    def ordinal(self, v):
        if self.published:
            if checkers.is_decimal(v):
                self._ordinal = v
            else:
                raise TypeError("the ordinal value must be a decimal.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def symbol(self):
        """
        Coded textual representation of this value in the enumeration,
        which may be strings made from “+” symbols, or other enumerations
        of terms such as “mild”, “moderate”, “severe”, or even the same number
        series as the values, e.g. “1”, “2”, “3”.
        """
        return self._symbol

    @symbol.setter
    def symbol(self, v):
        if self.published:
            if checkers.is_string(v):
                self._symbol = v
            else:
                raise TypeError("the symbol value must be a string.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def choices(self):
        """
        The choices dictionary uses a number for a key and a two member tuple
        for each choice item. The key is the 'ordinal', the first tuple member
        is the 'symbol' and the second member is a definition URL.

        Template:
        ordinal:(symbol, URI)
        """
        return self._choices

    @choices.setter
    def choices(self, v):
        if not self.published:
            if isinstance(v, dict):
                for k in v.keys():
                    if not isinstance(v[k], tuple) or len(v[k]) != 2:
                        raise TypeError("the item must be a 2 member tuple.")
                    if not isinstance(k, numbers.Number):
                        raise TypeError("the key must be a number.")
                    if not isinstance(v[k][1], str):
                        raise TypeError("the first member must be a string.")
                    if not isinstance(v[k][2], str):
                        raise TypeError("the second member must be a string (URI/URL).")

                self._choices = v
            else:
                raise TypeError("the choices value must be a dictionary.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not super(XdOrdinalType, self).validate():
            return(False)
        else:
            return(True)

    def getModel(self):
        """
        Return a XML Schema complexType definition.
        """
        self.validate()
        indent = 2
        padding = ('').rjust(indent)
        xdstr = super().getModel()

        ords = list(self._choices.keys())
        ords.sort()

        # XdOrdinal
        xdstr += padding.rjust(indent + 10) + ("<xs:element maxOccurs='1' minOccurs='1' name='ordinal'>\n")
        xdstr += padding.rjust(indent + 12) + ("<xs:simpleType>\n")
        xdstr += padding.rjust(indent + 12) + ("<xs:restriction base='xs:decimal'>\n")
        for k in ords:
            xdstr += padding.rjust(indent + 14) + ("<xs:enumeration value='" + str(k).strip() + "'/>\n")
        xdstr += padding.rjust(indent + 12) + ("</xs:restriction>\n")
        xdstr += padding.rjust(indent + 12) + ("</xs:simpleType>\n")
        xdstr += padding.rjust(indent + 10) + ("</xs:element>\n")

        xdstr += padding.rjust(indent + 10) + ("<xs:element maxOccurs='1' minOccurs='1' name='symbol'>\n")
        xdstr += padding.rjust(indent + 12) + ("<xs:simpleType>\n")
        xdstr += padding.rjust(indent + 14) + ("<xs:restriction base='xs:string'>\n")
        for k in ords:
            xdstr += padding.rjust(indent + 16) + ("<xs:enumeration value='" + str(self.choices[k][0]).strip() + "'>\n")
            xdstr += padding.rjust(indent + 16) + ("<xs:annotation>\n")
            xdstr += padding.rjust(indent + 18) + ("<xs:appinfo>\n")
            xdstr += padding.rjust(indent + 18) + ("<rdfs:Class rdf:about='mc-" + self.mcuid + "/symbol/" + quote(str(self.choices[k][0]).strip()) + "'>\n")
            xdstr += padding.rjust(indent + 20) + ("<rdfs:isDefinedBy rdf:resource='" + quote(str(self.choices[k][1]).strip()) + "'/>\n")
            xdstr += padding.rjust(indent + 18) + ("</rdfs:Class>\n")
            xdstr += padding.rjust(indent + 18) + ("</xs:appinfo>\n")
            xdstr += padding.rjust(indent + 16) + ("</xs:annotation>\n")
            xdstr += padding.rjust(indent + 16) + ("</xs:enumeration>\n")
        xdstr += padding.rjust(indent + 14) + ("</xs:restriction>\n")
        xdstr += padding.rjust(indent + 12) + ("</xs:simpleType>\n")
        xdstr += padding.rjust(indent + 10) + ("</xs:element>\n")
        xdstr += padding.rjust(indent + 8) + ("</xs:sequence>\n")
        xdstr += padding.rjust(indent + 6) + ("</xs:restriction>\n")
        xdstr += padding.rjust(indent + 4) + ("</xs:complexContent>\n")
        xdstr += padding.rjust(indent + 2) + ("</xs:complexType>\n\n")

        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an example XML fragment for this model.
        """
        if example == True:
            if not self.published:
                raise PublicationError("Cannot create an example unless the model is published.")
            c = choice(list(self._choices.keys()))
            self.ordinal = str(c)
            self.symbol = self._choices[c][0]
        else:
            if self.ordinal in list(self._choices.keys()):
                self.symbol = self._choices[self.ordinal][0]
            else:
                raise ValueError(str(self.ordinal) + " is not a valid ordinal.")

        indent = 2
        padding = ('').rjust(indent)
        xmlstr = super().getXMLInstance(example)
        xmlstr += padding.rjust(indent + 2) + '<ordinal>' + str(self.ordinal) + '</ordinal>\n'
        xmlstr += padding.rjust(indent + 2) + '<symbol>' + self.symbol + '</symbol>\n'
        xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.mcuid + '>\n'
        if self.adapter:
            xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.acuid + '>\n'

        return(xmlstr)


class XdQuantifiedType(XdOrderedType):
    """
    Serves as an abstract common ancestor of all quantifiable types
    """

    def __init__(self, label):
        super().__init__(label)

        self._magnitude_status = ''
        self._error = None
        self._accuracy = None
        self.cardinality = ('magnitude_status', [0, 1])
        self.cardinality = ('error', [0, 1])
        self.cardinality = ('accuracy', [0, 1])

    @property
    def magnitude_status(self):
        """
        MagnitudeStatus provides a general indication of the accuracy of the magnitude expressed in the XdQuantified
        subtypes. Should be used to inform users and not for decision support uses.
        Must be one of: None,'equal','less_than', 'greater_than', 'less_than_or_equal', 'greater_than_or_equal', 'approximate'
        """
        return self._magnitude_status

    @magnitude_status.setter
    def magnitude_status(self, v):
        if self.published:
            if isinstance(v, (str, None)) and v in [None, 'equal', 'less_than', 'greater_than', 'less_than_or_equal', 'greater_than_or_equal', 'approximate']:
                self._magnitude_status = v
            else:
                raise ValueError("The magnitude_status value must be one of: None,'equal','less_than', 'greater_than', 'less_than_or_equal', 'greater_than_or_equal', 'approximate'.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def error(self):
        """
        Error margin of measurement, as an integer indicating error in the recording method or instrument (+/- %).
        A logical value of 0 indicates 100% accuracy, i.e. no error.
        """
        return self._error

    @error.setter
    def error(self, v):
        if self.published:
            if isinstance(v, int) and 0 <= v <= 100:
                self._error = v
            else:
                raise TypeError("The error value must be an integer 0 - 100.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def accuracy(self):
        """
        Accuracy of the value in the magnitude attribute in the range 0% to (+/-)100%.
        A value of 0 means that the accuracy is unknown.
        """
        return self._accuracy

    @accuracy.setter
    def accuracy(self, v):
        if self.published:
            if isinstance(v, int) and 0 <= v <= 100:
                self._error = v
            else:
                raise TypeError("The accuracy value must be an integer 0 - 100.")
        else:
            raise PublicationError("The model has not been published.")

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not super(XdQuantifiedType, self).validate():
            return(False)
        else:
            return(True)

    def getModel(self):
        """
        Return a XML Schema complexType definition.
        """
        self.validate()
        indent = 2
        padding = ('').rjust(indent)

        xdstr = super().getModel()
        # XdQuantified
        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='0' name='magnitude-status' type='s3m:MagnitudeStatus'/>\n")
        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['error'][0]) + "' name='error'  type='xs:int' default='0'/>\n")
        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['accuracy'][0]) + "' name='accuracy' type='xs:int' default='0'/>\n")

        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an example XML fragment for this model.
        """

        indent = 4
        padding = ('').rjust(indent)
        xmlstr = super().getXMLInstance(example)
        if self.cardinality['magnitude_status'][0] > 0:
            xmlstr += padding.rjust(indent) + '<magnitude-status>=</magnitude-status>\n'
        if self.error is not None:
            xmlstr += padding.rjust(indent) + '<error>' + str(self.error).strip() + '</error>\n'
        if self.accuracy is not None:
            xmlstr += padding.rjust(indent) + '<accuracy>' + str(self.accuracy).strip() + '</accuracy>\n'

        return(xmlstr)


class XdCountType(XdQuantifiedType):
    """
    Countable quantities as an integer.

    Used for countable types such as pregnancies or steps taken by a
    physiotherapy patient, number of cigarettes smoked in a day, etc.

    The thing(s) being counted must be represented in the units element.

    Misuse: Not used for amounts of physical entities which all have
    standardized units as opposed to physical things counted.
    """

    def __init__(self, label: str):
        """
        The semantic label (name of the model) is required.
        """
        super().__init__(label)
        self._xdtype = "XdCountType"

        self._value = None
        self._units = None
        self.cardinality = ('value', [0, 1])
        self.cardinality = ('units', [1, 1])
        self._min_inclusive = None
        self._max_inclusive = None
        self._min_exclusive = None
        self._max_exclusive = None
        self._total_digits = None

        self._mag_constrained = not all([self._min_inclusive, self._max_inclusive, self._min_exclusive, self._max_exclusive, self._total_digits])

    @property
    def value(self):
        """
        Integer value of the counted items.
        """
        return self._value

    @value.setter
    def value(self, v):
        if self.published:
            if isinstance(v, (int, type(None))):
                if self.min_inclusive is not None and v < self.min_inclusive:
                    raise ValueError("The value cannot be less than " + str(self.min_inclusive))
                if self.max_inclusive is not None and v > self.max_inclusive:
                    raise ValueError("The value cannot exceed " + str(self.max_inclusive))
                if self.min_exclusive is not None and v <= self.min_exclusive:
                    raise ValueError("The value cannot be equal to or less than " + str(self.min_exclusive))
                if self.max_exclusive is not None and v >= self.max_exclusive:
                    raise ValueError("The value cannot be equal to or exceed " + str(self.max_exclusive))
                if self.total_digits is not None and len(str(v)) > self.total_digits:
                    raise ValueError("The value length cannot exceed " + str(self.total_digits) + " total digits.")

                self._value = v
            else:
                raise TypeError("The value value must be an integer.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def units(self):
        """
        The name or type of the items counted. Examples are cigarettes, drinks, pregnancies, episodes, etc.
        May or may not come from a standard terminology.
        """
        return self._units

    @units.setter
    def units(self, v):
        if not self.published:
            if isinstance(v, XdStringType):
                self._units = v
            else:
                self._units = None
                raise TypeError("The units value must be a XdStringType identifying the things to be counted.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def min_inclusive(self):
        """
        An inclusive minimum value.
        """
        return self._min_inclusive

    @min_inclusive.setter
    def min_inclusive(self, v):
        if not self.published:
            if isinstance(v, (int, type(None))):
                self._min_inclusive = v
            else:
                raise TypeError("The min_inclusive value must be an integer.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def max_inclusive(self):
        """
        An inclusive maximum value.
        """
        return self._max_inclusive

    @max_inclusive.setter
    def max_inclusive(self, v):
        if not self.published:
            if isinstance(v, (int, type(None))):
                self._max_inclusive = v
            else:
                raise TypeError("The max_inclusive value must be an integer.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def min_exclusive(self):
        """
        An exclusive minimum value.
        """
        return self._min_exclusive

    @min_exclusive.setter
    def min_exclusive(self, v):
        if not self.published:
            if isinstance(v, (int, type(None))):
                self._min_exclusive = v
            else:
                raise TypeError("The min_exclusive value must be an integer.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def max_exclusive(self):
        """
        An exclusive maximum value.
        """
        return self._max_exclusive

    @max_exclusive.setter
    def max_exclusive(self, v):
        if not self.published:
            if isinstance(v, (int, type(None))):
                self._max_exclusive = v
            else:
                raise TypeError("The max_exclusive value must be an integer.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def total_digits(self):
        """
        A maximum total digits constraint.
        """
        return self._total_digits

    @total_digits.setter
    def total_digits(self, v):
        if not self.published:
            if isinstance(v, (int, type(None))):
                self._total_digits = v
            else:
                raise TypeError("The total_digits value must be an integer.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not super(XdCountType, self).validate():
            return(False)
        else:
            if not isinstance(self.units, XdStringType):
                raise ValueError("Missing XdStringType for units.")

            return(True)

    def getModel(self):
        """
        Return a XML Schema complexType definition.
        """
        self.validate()
        indent = 2
        padding = ('').rjust(indent)

        xdstr = super().getModel()
        # XdCount
        if not self._mag_constrained:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['value'][0]) + "'  name='xdcount-value' type='xs:int'/>\n")
        else:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['value'][0]) + "'  name='xdcount-value'>\n")
            xdstr += padding.rjust(indent + 10) + ("<xs:simpleType>\n")
            xdstr += padding.rjust(indent + 10) + ("<xs:restriction base='xs:int'>\n")
            if self.min_inclusive is not None:
                xdstr += padding.rjust(indent + 12) + ("<xs:minInclusive value='" + str(self.min_inclusive).strip() + "'/>\n")
            if self.max_inclusive is not None:
                xdstr += padding.rjust(indent + 12) + ("<xs:maxInclusive value='" + str(self.max_inclusive).strip() + "'/>\n")
            if self.min_exclusive is not None:
                xdstr += padding.rjust(indent + 12) + ("<xs:minExclusive value='" + str(self.min_exclusive).strip() + "'/>\n")
            if self.max_exclusive is not None:
                xdstr += padding.rjust(indent + 12) + ("<xs:maxExclusive value='" + str(self.max_exclusive).strip() + "'/>\n")
            if (self.total_digits is not None and self.total_digits > 0):
                xdstr += padding.rjust(indent + 12) + ("<xs:totalDigits value='" + str(self.total_digits).strip() + "'/>\n")
            xdstr += padding.rjust(indent + 10) + ("</xs:restriction>\n")
            xdstr += padding.rjust(indent + 10) + ("</xs:simpleType>\n")
            xdstr += padding.rjust(indent + 8) + ("</xs:element>\n")

        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='1' name='xdcount-units' type='s3m:mc-" + str(self.units.mcuid) + "'/> \n")
        xdstr += padding.rjust(indent + 8) + ("</xs:sequence>\n")
        xdstr += padding.rjust(indent + 6) + ("</xs:restriction>\n")
        xdstr += padding.rjust(indent + 4) + ("</xs:complexContent>\n")
        xdstr += padding.rjust(indent + 2) + ("</xs:complexType>\n\n")
        xdstr += self.units.getModel()

        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an example XML fragment for this model.
        """
        if example == True and not isinstance(self.value, int):
            if not self.published:
                raise PublicationError("Cannot create an example unless the model is published.")
            if self.min_exclusive is not None:
                min = self.min_exclusive + 1
            elif self.min_inclusive is not None:
                min = self.min_inclusive
            else:
                min = 1

            if self.max_exclusive is not None:
                max = self.max_exclusive - 1
            elif self.max_inclusive is not None:
                max = self.max_inclusive
            else:
                max = 1000000000

            self.value = randint(min, max)

            if self.total_digits is not None:
                lenval = len(str(self.value))
                if lenval > self.total_digits:
                    self.value = int(str(self.value))[self.total_digits:]
            if self.units.value is None:
                if self.units.default is not None:
                    self.units.value = self.units.default
                elif len(self.units.enums) > 0:
                    self.units.value = choice(self.units.enums)
                else:
                    self.units.value = "Example Units"


        indent = 4
        padding = ('').rjust(indent)
        xmlstr = super().getXMLInstance(example)
        xmlstr += padding.rjust(indent) + '<xdcount-value>' + str(self.value).strip() + '</xdcount-value>\n'
        xmlstr += padding.rjust(indent) + '<xdcount-units>\n'
        xmlstr += padding.rjust(indent + 2) + '<label>' + self.units.label + '</label>\n'
        xmlstr += padding.rjust(indent + 2) + '<xdstring-value>' + self.units.value + '</xdstring-value>\n'
        xmlstr += padding.rjust(indent) + '</xdcount-units>\n'
        xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.mcuid + '>\n'
        if self.adapter:
            xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.acuid + '>\n'

        return(xmlstr)


class XdQuantityType(XdQuantifiedType):
    """
    Quantified type representing specific quantities, i.e. quantities expressed as a magnitude and units. Can also be used for time durations, where it is more convenient to treat these as simply a number of individual seconds, minutes, hours, days, months, years, etc. when no temporal calculation is to be performed.
    """

    def __init__(self, label):
        """
        The semantic label (name of the model) is required.
        """
        super().__init__(label)
        self._xdtype = "XdQuantityType"

        self._value = None
        self._units = None
        self.cardinality = ('value', [0, 1])
        self.cardinality = ('units', [1, 1])
        self._min_inclusive = None
        self._max_inclusive = None
        self._min_exclusive = None
        self._max_exclusive = None
        self._total_digits = None
        self._fraction_digits = None
        self._mag_constrained = not all([self._min_inclusive, self._max_inclusive, self._min_exclusive, self._max_exclusive, self._total_digits, self._fraction_digits])

    @property
    def value(self):
        """
        Numeric value of the quantity.
        """
        return self._value

    @value.setter
    def value(self, v):
        if self.published:
            if v is not None and isinstance(v, (int, float)):
                v = Decimal(str(v))
            if isinstance(v, (Decimal, type(None))):
                if self.min_inclusive is not None and v < self.min_inclusive:
                    raise ValueError("The value cannot be less than " + str(self.min_inclusive))
                if self.max_inclusive is not None and v > self.max_inclusive:
                    raise ValueError("The value cannot exceed " + str(self.max_inclusive))
                if self.min_exclusive is not None and v <= self.min_exclusive:
                    raise ValueError("The value cannot be equal to or less than " + str(self.min_exclusive))
                if self.max_exclusive is not None and v >= self.max_exclusive:
                    raise ValueError("The value cannot be equal to or exceed " + str(self.max_exclusive))
                if self.total_digits is not None and len(str(v)) > self.total_digits:
                    raise ValueError("The value length cannot exceed " + str(self.total_digits) + " total digits. Value = " + str(self.value))
                if self.fraction_digits is not None and len(str(v).split('.')[1]) > self.fraction_digits:
                    raise ValueError("The length of the decimal places in the value cannot exceed " + str(self.fraction_digits) + " fraction digits. Value = " + str(self.value))
                self._value = v
            else:
                raise ValueError("The value must be a decimal.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def units(self):
        """
        The name or type of the quantity. Examples are "kg/m2", “mmHg", "ms-1", "km/h".
        May or may not come from a standard terminology.
        """
        return self._units

    @units.setter
    def units(self, v):
        if not self.published:
            if isinstance(v, XdStringType):
                self._units = v
            else:
                raise ValueError("The units value must be a XdStringType identifying the things to be measured.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def min_inclusive(self):
        """
        An inclusive minimum value.
        """
        return self._min_inclusive

    @min_inclusive.setter
    def min_inclusive(self, v):
        if not self.published:
            if v is not None and isinstance(v, int):
                v = Decimal(v)
            if isinstance(v, (Decimal, type(None))):
                self._min_inclusive = v
            else:
                raise ValueError("The min_inclusive value must be a Decimal.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def max_inclusive(self):
        """
        An inclusive maximum value.
        """
        return self._max_inclusive

    @max_inclusive.setter
    def max_inclusive(self, v):
        if not self.published:
            if v is not None and isinstance(v, int):
                v = Decimal(v)
            if isinstance(v, (Decimal, type(None))):
                self._max_inclusive = v
            else:
                raise ValueError("The max_inclusive value must be a Decimal.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def min_exclusive(self):
        """
        An exclusive minimum value.
        """
        return self._min_exclusive

    @min_exclusive.setter
    def min_exclusive(self, v):
        if not self.published:
            if v is not None and isinstance(v, int):
                v = Decimal(v)
            if isinstance(v, (Decimal, type(None))):
                self._min_exclusive = v
            else:
                raise ValueError("The min_exclusive value must be a Decimal.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def max_exclusive(self):
        """
        An exclusive maximum value.
        """
        return self._max_exclusive

    @max_exclusive.setter
    def max_exclusive(self, v):
        if not self.published:
            if v is not None and isinstance(v, int):
                v = Decimal(v)
            if isinstance(v, (Decimal, type(None))):
                self._max_exclusive = v
            else:
                raise ValueError("The max_exclusive value must be a Decimal.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def total_digits(self):
        """
        A maximum total digits constraint.
        """
        return self._total_digits

    @total_digits.setter
    def total_digits(self, v):
        if not self.published:
            if isinstance(v, (int, type(None))):
                self._total_digits = v
            else:
                raise ValueError("The total_digits value must be a integer.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def fraction_digits(self):
        """
        A maximum fraction digits constraint.
        """
        return self._fraction_digits

    @fraction_digits.setter
    def fraction_digits(self, v):
        if not self.published:
            if isinstance(v, (int, type(None))):
                self._fraction_digits = v
            else:
                raise ValueError("The fraction_digits value must be a integer.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not super(XdQuantityType, self).validate():
            return(False)
        else:
            if not isinstance(self.units, XdStringType):
                raise ValueError("Missing XdStringType for units.")
            return(True)

    def getModel(self):
        """
        Return a XML Schema complexType definition.
        """
        self.validate()
        indent = 2
        padding = ('').rjust(indent)

        xdstr = super().getModel()
        # XdQuantity
        if not self._mag_constrained:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['value'][0]) + "'  name='xdquantity-value' type='xs:decimal'/>\n")
        else:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['value'][0]) + "'  name='xdquantity-value'>\n")
            xdstr += padding.rjust(indent + 10) + ("<xs:simpleType>\n")
            xdstr += padding.rjust(indent + 10) + ("<xs:restriction base='xs:decimal'>\n")
            if self.min_inclusive is not None:
                xdstr += padding.rjust(indent + 12) + ("<xs:minInclusive value='" + str(self.min_inclusive).strip() + "'/>\n")
            if self.max_inclusive is not None:
                xdstr += padding.rjust(indent + 12) + ("<xs:maxInclusive value='" + str(self.max_inclusive).strip() + "'/>\n")
            if self.min_exclusive is not None:
                xdstr += padding.rjust(indent + 12) + ("<xs:minExclusive value='" + str(self.min_exclusive).strip() + "'/>\n")
            if self.max_exclusive is not None:
                xdstr += padding.rjust(indent + 12) + ("<xs:maxExclusive value='" + str(self.max_exclusive).strip() + "'/>\n")
            if (self.total_digits is not None and self.total_digits > 0):
                xdstr += padding.rjust(indent + 12) + ("<xs:totalDigits value='" + str(self.total_digits).strip() + "'/>\n")
            if (self.fraction_digits is not None and self.fraction_digits >= 0):
                xdstr += padding.rjust(indent + 12) + ("<xs:fractionDigits value='" + str(self.fraction_digits).strip() + "'/>\n")
            xdstr += padding.rjust(indent + 10) + ("</xs:restriction>\n")
            xdstr += padding.rjust(indent + 10) + ("</xs:simpleType>\n")
            xdstr += padding.rjust(indent + 8) + ("</xs:element>\n")

        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='1' name='xdquantity-units' type='s3m:mc-" + str(self.units.mcuid) + "'/> \n")
        xdstr += padding.rjust(indent + 8) + ("</xs:sequence>\n")
        xdstr += padding.rjust(indent + 6) + ("</xs:restriction>\n")
        xdstr += padding.rjust(indent + 4) + ("</xs:complexContent>\n")
        xdstr += padding.rjust(indent + 2) + ("</xs:complexType>\n\n")

        if len(self.referenceranges) > 0:
            for rr in self.referenceranges:
                xdstr += rr.getModel()

        xdstr += self.units.getModel()

        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an example XML fragment for this model.
        """

        if example == True and self.value == None:
            if not self.published:
                raise PublicationError("Cannot create an example unless the model is published.")
            start = 1 if self.min_inclusive == None else self.min_inclusive
            end = 100000 if self.max_inclusive == None else self.max_inclusive
            val = str(uniform(float(start), float(end)))

            if isinstance(self.fraction_digits, int):
                ipart = val.split('.')[0]
                fpart = val.split('.')[1][:self.fraction_digits]
                val = ipart + '.' + fpart

            if isinstance(self.total_digits, int):
                if len(val) > self.total_digits:
                    val = val[self.total_digits:]

            self.value = Decimal(val)

            if self.units.value is None:
                if self.units.default is not None:
                    self.units.value = self.units.default
                elif len(self.units.enums) > 0:
                    self.units.value = choice(self.units.enums)
                else:
                    self.units.value = "Example Units"


        indent = 4
        padding = ('').rjust(indent)
        xmlstr = super().getXMLInstance(example)
        xmlstr += padding.rjust(indent) + '<xdquantity-value>' + str(self.value).strip() + '</xdquantity-value>\n'
        xmlstr += padding.rjust(indent) + '<xdquantity-units>\n'
        xmlstr += padding.rjust(indent + 2) + '<label>' + self.units.label + '</label>\n'
        xmlstr += padding.rjust(indent + 2) + '<xdstring-value>' + self.units.value + '</xdstring-value>\n'
        xmlstr += padding.rjust(indent) + '</xdquantity-units>\n'
        xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.mcuid + '>\n'
        if self.adapter:
            xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.acuid + '>\n'


        return(xmlstr)


class XdFloatType(XdQuantifiedType):
    """
    Quantified type representing specific a value as a floating point,
    64 bit or sometimes called a double (XML Schema), number and optional units.

    This type accepts several "special" values:
    - positive zero (0)
    - negative zero (-0) (which is greater than positive 0 but less than any negative value)
    - infinity (INF) (which is greater than any value)
    - negative infinity (-INF) (which is less than any float
    - "not a number" (NaN) case-sensitive
    """

    # TODO: Fully test the Python 3.x implementation vs. the XML Schema implementation

    def __init__(self, label):
        """
        The semantic label (name of the model) is required.
        """
        super().__init__(label)
        self._xdtype = "XdFloatType"

        self._value = None
        self._units = None
        self.cardinality = ('value', [0, 1])
        self.cardinality = ('units', [0, 1])
        self._min_inclusive = None
        self._max_inclusive = None
        self._min_exclusive = None
        self._max_exclusive = None
        self._mag_constrained = not all([self._min_inclusive, self._max_inclusive, self._min_exclusive, self._max_exclusive])

    @property
    def value(self):
        """
        Float value.
        """
        return self._value

# TODO: fix the decimal places to follow the fractions digits
    @value.setter
    def value(self, v):
        if self.published:
            if isinstance(v, float):
                self._value = v
            else:
                raise ValueError("The value must be a float.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def units(self):
        """
        The name or type of the float value.
        """
        return self._units

    @units.setter
    def units(self, v):
        if not self.published:
            if isinstance(v, XdStringType):
                self._units = v
            else:
                raise ValueError("The units value must be a XdStringType identifying the things to be measured.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def min_inclusive(self):
        """
        An inclusive minimum value.
        """
        return self._min_inclusive

    @min_inclusive.setter
    def min_inclusive(self, v):
        if not self.published:
            v = float(v)
            if isinstance(v, float):
                self._min_inclusive = v
            else:
                raise ValueError("The min_inclusive value must be a float.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def max_inclusive(self):
        """
        An inclusive maximum value.
        """
        return self._max_inclusive

    @max_inclusive.setter
    def max_inclusive(self, v):
        if not self.published:
            v = float(v)
            if isinstance(v, float):
                self._max_inclusive = v
            else:
                raise ValueError("The max_inclusive value must be a float.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def min_exclusive(self):
        """
        An exclusive minimum value.
        """
        return self._min_exclusive

    @min_exclusive.setter
    def min_exclusive(self, v):
        if not self.published:
            v = float(v)
            if isinstance(v, float):
                self._min_exclusive = v
            else:
                raise ValueError("The min_exclusive value must be a float.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def max_exclusive(self):
        """
        An exclusive maximum value.
        """
        return self._max_exclusive

    @max_exclusive.setter
    def max_exclusive(self, v):
        if not self.published:
            v = float(v)
            if isinstance(v, float):
                self._max_exclusive = v
            else:
                raise ValueError("The max_exclusive value must be a float.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")


    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not super(XdFloatType, self).validate():
            return(False)
        else:
            if self.units is not None and not isinstance(self.units, XdStringType):
                raise TypeError("Incorrect units definition.")
            return(True)

    def getModel(self):
        """
        Return a XML Schema complexType definition.
        """
        self.validate()
        indent = 2
        padding = ('').rjust(indent)

        xdstr = super().getModel()
        # XdFloat
        if not self._mag_constrained:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['value'][0]) + "'  name='xdfloat-value' type='xs:float'/>\n")
        else:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['value'][0]) + "'  name='xdfloat-value'>\n")
            xdstr += padding.rjust(indent + 10) + ("<xs:simpleType>\n")
            xdstr += padding.rjust(indent + 10) + ("<xs:restriction base='xs:float'>\n")
            if self.min_inclusive is not None:
                xdstr += padding.rjust(indent + 12) + ("<xs:minInclusive value='" + str(self.min_inclusive).strip() + "'/>\n")
            if self.max_inclusive is not None:
                xdstr += padding.rjust(indent + 12) + ("<xs:maxInclusive value='" + str(self.max_inclusive).strip() + "'/>\n")
            if self.min_exclusive is not None:
                xdstr += padding.rjust(indent + 12) + ("<xs:minExclusive value='" + str(self.min_exclusive).strip() + "'/>\n")
            if self.max_exclusive is not None:
                xdstr += padding.rjust(indent + 12) + ("<xs:maxExclusive value='" + str(self.max_exclusive).strip() + "'/>\n")
            xdstr += padding.rjust(indent + 10) + ("</xs:restriction>\n")
            xdstr += padding.rjust(indent + 10) + ("</xs:simpleType>\n")
            xdstr += padding.rjust(indent + 8) + ("</xs:element>\n")

        if self.units:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['units'][0]) + "' name='xdfloat-units' type='s3m:mc-" + str(self.units.mcuid) + "'/> \n")
        xdstr += padding.rjust(indent + 8) + ("</xs:sequence>\n")
        xdstr += padding.rjust(indent + 6) + ("</xs:restriction>\n")
        xdstr += padding.rjust(indent + 4) + ("</xs:complexContent>\n")
        xdstr += padding.rjust(indent + 2) + ("</xs:complexType>\n\n")
        if self.units:
            xdstr += self.units.getModel()

        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an example XML fragment for this model.
        """
        # TODO: Improve sample generation using other facets
        if example == True and self.value == None:
            if not self.published:
                raise PublicationError("Cannot create an example unless the model is published.")
            start = 1 if self.min_inclusive == None else self.min_inclusive
            end = 1000 if self.max_inclusive == None else self.max_inclusive
            val = uniform(float(start), float(end))
            self.value = val

            if self.units.value is None:
                if self.units.default is not None:
                    self.units.value = self.units.default
                elif len(self.units.enums) > 0:
                    self.units.value = choice(self.units.enums)
                else:
                    self.units.value = "Example Units"


        if self.value == None:
            self.value = float("NaN")

        indent = 4
        padding = ('').rjust(indent)
        xmlstr = super().getXMLInstance(example)
        xmlstr += padding.rjust(indent) + '<xdfloat-value>' + str(self.value).strip() + '</xdfloat-value>\n'
        if self.units:
            xmlstr += padding.rjust(indent) + '<xdfloat-units>\n'
            xmlstr += padding.rjust(indent + 2) + '<label>' + self.units.label + '</label>\n'
            xmlstr += padding.rjust(indent + 2) + '<xdstring-value>' + self.units.value + '</xdstring-value>\n'
            xmlstr += padding.rjust(indent) + '</xdfloat-units>\n'
        xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.mcuid + '>\n'
        if self.adapter:
            xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.acuid + '>\n'


        return(xmlstr)

class XdRatioType(XdQuantifiedType):
    """
    Models a ratio of values, i.e. where the numerator and denominator are both pure numbers.

    Should not be used for formulations. Used for modeling; ratios, rates or proportions.
    """

    def __init__(self, label):
        """
        The semantic label (name of the model) is required.
        """
        super().__init__(label)
        self._xdtype = "XdRatioType"

        self._ratio_type = None

        self._numerator = None
        self._num_min_inclusive = None
        self._num_max_inclusive = None
        self._num_min_exclusive = None
        self._num_max_exclusive = None

        self._denominator = None
        self._den_min_inclusive = None
        self._den_max_inclusive = None
        self._den_min_exclusive = None
        self._den_max_exclusive = None

        self._ratio_value = None

        self._numerator_units = None
        self._denominator_units = None
        self._ratio_units = None

        self.cardinality = ('numerator', [0, 1])
        self.cardinality = ('denominator', [0, 1])
        self.cardinality = ('value', [0, 1])
        self.cardinality = ('numerator_units', [0, 1])
        self.cardinality = ('denominator_units', [0, 1])
        self.cardinality = ('ratio_units', [0, 1])

    @property
    def ratio_type(self):
        """
        Indicates specific type of ratio modeled in the DM as a 'ratio','rate', or 'proportion'.
        """
        return self._ratio_type

    @ratio_type.setter
    def ratio_type(self, v):
        if not self.published:
            if isinstance(v, str) and v.lower() in ['ratio', 'rate', 'proportion']:
                self._ratio_type = v.lower()
            else:
                raise ValueError("The ratio_type value must be a str and be one of; 'ratio','rate', or 'proportion'.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def ratio(self):
        """
        Numerator of ratio.
        """
        return self._ratio_value

    @ratio.setter
    def ratio(self, v):
        if self.published:
            if isinstance(v, float):
                self._ratio_value = v
            else:
                raise ValueError("The ratio value must be a float.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def numerator(self):
        """
        Numerator of ratio.
        """
        return self._numerator

    @numerator.setter
    def numerator(self, v):
        if self.published:
            if isinstance(v, float):
                self._numerator = v
            else:
                raise ValueError("The numerator value must be a float.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def num_min_inclusive(self):
        """
        An inclusive minimum value.
        """
        return self._num_min_inclusive

    @num_min_inclusive.setter
    def num_min_inclusive(self, v):
        if not self.published:
            if v is not None and isinstance(v, int):
                v = Decimal(v)
            if isinstance(v, (Decimal, type(None))):
                self._num_min_inclusive = v
            else:
                raise ValueError("The min_inclusive value must be a Decimal.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def num_max_inclusive(self):
        """
        An inclusive maximum value.
        """
        return self._num_max_inclusive

    @num_max_inclusive.setter
    def num_max_inclusive(self, v):
        if not self.published:
            if v is not None and isinstance(v, int):
                v = Decimal(v)
            if isinstance(v, (Decimal, type(None))):
                self._num_max_inclusive = v
            else:
                raise ValueError("The max_inclusive value must be a Decimal.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def num_min_exclusive(self):
        """
        An exclusive minimum value.
        """
        return self._num_min_exclusive

    @num_min_exclusive.setter
    def num_min_exclusive(self, v):
        if not self.published:
            if v is not None and isinstance(v, int):
                v = Decimal(v)
            if isinstance(v, (Decimal, type(None))):
                self._num_min_exclusive = v
            else:
                raise ValueError("The min_exclusive value must be a Decimal.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def num_max_exclusive(self):
        """
        An exclusive maximum value.
        """
        return self._num_max_exclusive

    @num_max_exclusive.setter
    def num_max_exclusive(self, v):
        if not self.published:
            if v is not None and isinstance(v, int):
                v = Decimal(v)
            if isinstance(v, (Decimal, type(None))):
                self._num_max_exclusive = v
            else:
                raise ValueError("The max_exclusive value must be a Decimal.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def denominator(self):
        """
        Denominator of ratio.
        """
        return self._denominator

    @denominator.setter
    def denominator(self, v):
        if self.published:
            if isinstance(v, float):
                self._denominator = v
            else:
                raise ValueError("The denominator value must be a float.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def den_min_inclusive(self):
        """
        An inclusive minimum value.
        """
        return self._den_min_inclusive

    @den_min_inclusive.setter
    def den_min_inclusive(self, v):
        if v is not None and isinstance(v, int):
            v = Decimal(v)
        if isinstance(v, (Decimal, type(None))):
            self._den_min_inclusive = v
        else:
            raise ValueError("The den_min_inclusive value must be a Decimal.")

    @property
    def den_max_inclusive(self):
        """
        An inclusive maximum value.
        """
        return self._den_max_inclusive

    @den_max_inclusive.setter
    def den_max_inclusive(self, v):
        if v is not None and isinstance(v, int):
            v = Decimal(v)
        if isinstance(v, (Decimal, type(None))):
            self._den_max_inclusive = v
        else:
            raise ValueError("The den_max_inclusive value must be a Decimal.")

    @property
    def den_min_exclusive(self):
        """
        An exclusive minimum value.
        """
        return self._den_min_exclusive

    @den_min_exclusive.setter
    def den_min_exclusive(self, v):
        if v is not None and isinstance(v, int):
            v = Decimal(v)
        if isinstance(v, (Decimal, type(None))):
            self._den_min_exclusive = v
        else:
            raise ValueError("The den_min_exclusive value must be a Decimal.")

    @property
    def den_max_exclusive(self):
        """
        An exclusive maximum value.
        """
        return self._den_max_exclusive

    @den_max_exclusive.setter
    def den_max_exclusive(self, v):
        if v is not None and isinstance(v, int):
            v = Decimal(v)
        if isinstance(v, (Decimal, type(None))):
            self._den_max_exclusive = v
        else:
            raise ValueError("The den_max_exclusive value must be a Decimal.")

    @property
    def numerator_units(self):
        """
        Used to convey the meaning of the numerator. Typically countable units such as; cigarettes, drinks,
        exercise periods, etc. May or may not come from a terminology.
        """
        return self._numerator_units

    @numerator_units.setter
    def numerator_units(self, v):
        if not self.published:
            if isinstance(v, XdStringType):
                self._numerator_units = v
            else:
                raise ValueError("The numerator_units value must be a XdStringType.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def denominator_units(self):
        """
        Used to convey the meaning of the denominator. Typically units such as; minutes, hours, days, years, months, etc.
        May or may not come from a standard terminology.
        """
        return self._denominator_units

    @denominator_units.setter
    def denominator_units(self, v):
        if not self.published:
            if isinstance(v, XdStringType):
                self._denominator_units = v
            else:
                raise ValueError("The denominator_units value must be a XdStringType.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    @property
    def ratio_units(self):
        """
        Used to convey the meaning of the ratio.
        """
        return self._ratio_units

    @ratio_units.setter
    def ratio_units(self, v):
        if not self.published:
            if isinstance(v, XdStringType):
                self._ratio_units = v
            else:
                raise ValueError("The ratio_units value must be a XdStringType.")
        else:
            raise PublicationError("The model has been published and cannot be edited.")

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not super(XdRatioType, self).validate():
            return(False)
        else:
            return(True)

    def getModel(self):
        """
        Return a XML Schema complexType definition.
        """
        self.validate()
        indent = 2
        padding = ('').rjust(indent)

        xdstr = super().getModel()
        # XdRatio

        # tests for proper modelling
        if (self.num_min_inclusive and self.num_min_exclusive) or (self.num_max_inclusive and self.num_max_exclusive):
            raise ValueError(self.__str__() + ": There is ambiguity in your numerator constraints for min/max. Please use EITHER minimum or maximum values, not both.", messages.ERROR)

        if (self.den_min_inclusive and self.den_min_exclusive) or (self.den_max_inclusive and self.den_max_exclusive):
            raise ValueError(self.__str__() + ": There is ambiguity in your denominator constraints for min/max. Please use EITHER minimum or maximum values, not both.", messages.ERROR)


        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='1' name='ratio-type' type='s3m:TypeOfRatio'/>\n")
        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['numerator'][0]) + "' name='numerator'>\n")
        xdstr += padding.rjust(indent + 10) + ("<xs:simpleType>\n")
        xdstr += padding.rjust(indent + 10) + ("<xs:restriction base='xs:float'>\n")
        if self.num_min_inclusive:
            xdstr += padding.rjust(indent + 12) + ("<xs:minInclusive value='" + str(self.num_min_inclusive).strip() + "'/>\n")
        if self.num_min_exclusive:
            xdstr += padding.rjust(indent + 12) + ("<xs:minExclusive value='" + str(self.num_min_exclusive).strip() + "'/>\n")
        if self.num_max_inclusive:
            xdstr += padding.rjust(indent + 12) + ("<xs:maxInclusive value='" + str(self.num_max_inclusive).strip() + "'/>\n")
        if self.num_max_exclusive:
            xdstr += padding.rjust(indent + 12) + ("<xs:maxExclusive value='" + str(self.num_max_exclusive).strip() + "'/>\n")
        xdstr += padding.rjust(indent + 10) + ("</xs:restriction>\n")
        xdstr += padding.rjust(indent + 10) + ("</xs:simpleType>\n")
        xdstr += padding.rjust(indent + 8) + ("</xs:element>\n")

        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['denominator'][0]) + "' name='denominator'>\n")
        xdstr += padding.rjust(indent + 10) + ("<xs:simpleType>\n")
        xdstr += padding.rjust(indent + 10) + ("<xs:restriction base='xs:float'>\n")
        if self.den_min_inclusive is not None:
            xdstr += padding.rjust(indent + 12) + ("<xs:minInclusive value='" + str(self.den_min_inclusive).strip() + "'/>\n")
        if self.den_min_exclusive is not None:
            xdstr += padding.rjust(indent + 12) + ("<xs:minExclusive value='" + str(self.den_min_exclusive).strip() + "'/>\n")
        if self.den_max_inclusive is not None:
            xdstr += padding.rjust(indent + 12) + ("<xs:maxInclusive value='" + str(self.den_max_inclusive).strip() + "'/>\n")
        if self.den_max_exclusive is not None:
            xdstr += padding.rjust(indent + 12) + ("<xs:maxExclusive value='" + str(self.den_max_exclusive).strip() + "'/>\n")
        xdstr += padding.rjust(indent + 10) + ("</xs:restriction>\n")
        xdstr += padding.rjust(indent + 10) + ("</xs:simpleType>\n")
        xdstr += padding.rjust(indent + 8) + ("</xs:element>\n")

        if self.numerator_units:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['numerator_units'][0]) + "' name='numerator-units' type='s3m:mc-" + self.numerator_units.mcuid + "'/> \n")

        if self.denominator_units:
            xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='1' minOccurs='" + str(self.cardinality['denominator_units'][0]) + "' name='denominator-units' type='s3m:mc-" + self.denominator_units.mcuid + "'/>\n")
        xdstr += padding.rjust(indent + 8) + ("</xs:sequence>\n")
        xdstr += padding.rjust(indent + 6) + ("</xs:restriction>\n")
        xdstr += padding.rjust(indent + 4) + ("</xs:complexContent>\n")
        xdstr += padding.rjust(indent + 2) + ("</xs:complexType>\n\n")

        if self.numerator_units:
            xdstr += self.numerator_units.getModel()
        if self.denominator_units:
            xdstr += self.denominator_units.getModel()

        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an XML fragment for this model.
        """
        if example == True:
            if not self.published:
                raise PublicationError("Cannot create an example unless the model is published.")
            start = 1 if self.num_min_inclusive == None else self.num_min_inclusive
            end = 100000 if self.num_max_inclusive == None else self.num_max_inclusive
            self.numerator = uniform(float(start), float(end))
            start = 1 if self.den_min_inclusive == None else self.den_min_inclusive
            end = 100000 if self.den_max_inclusive == None else self.den_max_inclusive
            self.denominator = uniform(float(start), float(end))
            self.ratio = float(self.numerator / self.denominator)

            if self.numerator_units.value is None:
                if self.numerator_units.default is not None:
                    self.numerator_units.value = self.numerator_units.default
                elif len(self.numerator_units.enums) > 0:
                    self.numerator_units.value = choice(self.numerator_units.enums)[0]
                else:
                    self.numerator_units.value = "Numerator Units"
            if self.denominator_units.value is None:
                if self.denominator_units.default is not None:
                    self.denominator_units.value = self.denominator_units.default
                elif len(self.denominator_units.enums) > 0:
                    self.denominator_units.value = choice(self.denominator_units.enums)[0]
                else:
                    self.denominator_units.value = "Denominator Units"

        indent = 2
        padding = ('').rjust(indent)
        xmlstr = super().getXMLInstance(example)

        xmlstr += padding + "<ratio-type>" + self.ratio_type + "</ratio-type>\n"
        xmlstr += padding + "<numerator>" + str(self.numerator) + "</numerator>\n"
        xmlstr += padding + "<denominator>" + str(self.denominator) + "</denominator>\n"
        xmlstr += padding + "<xdratio-value>" + str(self.ratio) + "</xdratio-value>\n"
        if self.numerator_units is not None:
            xmlstr += padding + "<numerator-units>\n"
            xmlstr += padding + "  <label>" + escape(self.numerator_units.label) + "</label>\n"
            xmlstr += padding + "  <xdstring-value>" + self.numerator_units.value + "</xdstring-value>\n"
            xmlstr += padding + "</numerator-units>\n"
        if self.denominator_units is not None:
            xmlstr += padding + "<denominator-units>\n"
            xmlstr += padding + "  <label>" + escape(self.denominator_units.label) + "</label>\n"
            xmlstr += padding + "  <xdstring-value>" + self.denominator_units.value + "</xdstring-value>\n"
            xmlstr += padding + "</denominator-units>\n"
        if self.ratio_units is not None:
            xmlstr += padding + "<xdratio-units>\n"
            xmlstr += padding + "  <label>" + escape(self.ratio_units.label) + "</label>\n"
            xmlstr += padding + "  <xdstring-value>" + self.ratio_units.value + "</xdstring-value>\n"
            xmlstr += padding + "</xdratio-units>\n"

        xmlstr += padding + "</s3m:ms-" + str(self.mcuid) + ">\n"
        if self.adapter:
            xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.acuid + '>\n'

        return(xmlstr)

class XdTemporalType(XdOrderedType):
    """
    Type defining the concept of date and time types.
    Must be constrained in DMs to be one or more of the below elements.
    This gives the modeler the ability to optionally allow one or more types of temporal content such as
    full or partial dates at run time.
    Setting cardinality of both max and min to zero causes the element to be prohibited.
    """

    def __init__(self, label):
        """
        The semantic label (name of the model) is required.
        """
        super().__init__(label)
        self._xdtype = "XdTemporalType"

        self._date = None
        self._time = None
        self._datetime = None
        self._day = None
        self._month = None
        self._year = None
        self._year_month = None
        self._month_day = None
        self._duration = None
        self.cardinality = ('date', [0, 1])
        self.cardinality = ('time', [0, 1])
        self.cardinality = ('datetime', [0, 1])
        self.cardinality = ('day', [0, 1])
        self.cardinality = ('month', [0, 1])
        self.cardinality = ('year', [0, 1])
        self.cardinality = ('year_month', [0, 1])
        self.cardinality = ('month_day', [0, 1])
        self.cardinality = ('duration', [0, 1])

        # self.allow_duration and (self.allow_date or self.allow_time or self.allow_datetime or self.allow_day or self.allow_month or self.allow_year or self.allow_year_month or self.allow_month_day):

    @property
    def date(self):
        """
        Represents top-open intervals of exactly one day in length on the timelines of dateTime,
        beginning on the beginning moment of each day, up to but not including the beginning moment of the next day).
        For non-timezoned values, the top-open intervals disjointly cover the non-timezoned timeline, one per day.
        For timezoned values, the intervals begin at every minute and therefore overlap.
        When serialized to XML or JSON the ISO format YYYY-MM-DD is used.
        """
        return self._date

    @date.setter
    def date(self, v):
        if self.published:
            if isinstance(v, (date, type(None))):
                self._date = v
            else:
                raise ValueError("The date value must be a date type.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def time(self):
        """
        Represents instants of time (with or without a timezone) that recur at the same point in each calendar day, or that occur in some
        arbitrary calendar day.
        """
        return self._time

    @time.setter
    def time(self, v):
        if self.published:
            if isinstance(v, (time, type(None))):
                self._time = v
            else:
                raise ValueError("The time value must be a time type.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def datetime(self):
        """
        Represents instants of time, optionally marked with a particular time zone offset.
        Values representing the same instant but having different time zone offsets are equal but not identical.
        """
        return self._datetime

    @datetime.setter
    def datetime(self, v):
        if self.published:
            if isinstance(v, (datetime, type(None))):
                self._datetime = v
            else:
                raise ValueError("The datetime value must be a datetime type.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def day(self):
        """
        Represents whole days within an arbitrary month—days that recur at the same point in each (Gregorian) month.
        This datatype is used to represent a specific day of the month as an integer.
        To indicate, for example, that an employee gets a paycheck on the 15th of each month.
        (Obviously, days beyond 28 cannot occur in all months; they are nonetheless permitted, up to 31.)
        """
        return self._day

    @day.setter
    def day(self, v):
        if self.published:
            if isinstance(v, type(None)) or isinstance(v, int) and 1 <= v <= 31:
                self._day = v
            else:
                raise ValueError("The day value must be an integer type 1 - 31.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def month(self):
        """
        Represents whole (Gregorian) months within an arbitrary year—months that recur at the same point in each year.
        It might be used, for example, to say what month annual Thanksgiving celebrations fall in different
        countries (11 in the United States, 10 in Canada, and possibly other months in other countries).
        """
        return self._month

    @month.setter
    def month(self, v):
        if self.published:
            if isinstance(v, type(None)) or isinstance(v, int) and 1 <= v <= 12:
                self._month = v
            else:
                raise ValueError("The month value must be an integer type 1 - 12.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def year(self):
        """
        Represents Gregorian calendar years.
        """
        return self._year

    @year.setter
    def year(self, v):
        if self.published:
            if isinstance(v, type(None)) or isinstance(v, int) and 1 <= v <= 9999:
                self._year = v
            else:
                raise ValueError("The year value must be an integer type 1 - 9999.")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def year_month(self):
        """
        Represents specific whole Gregorian months in specific Gregorian years.
        Represented as a tuple of integers (YYYY, MM).
        """
        return self._year_month

    @year_month.setter
    def year_month(self, v):
        if self.published:
            if isinstance(v, type(None)):
                self._year_month = v
            elif isinstance(v, tuple):
                if not 1 <= v[0] <= 9999 or not 1 <= v[1] <= 12:
                    raise ValueError("The year_month value must be a tuple of integers representing 1 <= yyyy <= 9999 and 1 <= dd <= 12.")
                self._year_month = v
            else:
                raise ValueError("The year_month value must be a tuple of integers representing (yyyy,mm).")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def month_day(self):
        """
        Represents whole calendar days that recur at the same point in each calendar year, or that occur in some
        arbitrary calendar year.
        (Obviously, days beyond 28 cannot occur in all Februaries; 29 is nonetheless permitted in February.)
        """
        return self._month_day

    @month_day.setter
    def month_day(self, v):
        if self.published:
            max_days = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
            if isinstance(v, type(None)):
                self._month_day = v
            elif isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], int) and isinstance(v[1], int):
                if v[1] > max_days[v[0]]:
                    raise ValueError("The day value must be must be less than or equal to the number of days allowed in the month.")
                self._month_day = v
            else:
                raise ValueError("The month_day value must be a tuple of integers representing (mm,dd).")
        else:
            raise PublicationError("The model has not been published.")

    @property
    def duration(self):
        """
        A datatype that represents durations of time. The concept of duration being captured is drawn from those of
        ISO-8601, specifically durations without fixed endpoints.
        For example, "15 days" (whose most common lexical representation in duration is "'P15D'") is a duration value.
        However, "15 days beginning 12 July 1995" and "15 days ending 12 July 1995" are not duration values.
        This datatype can provide addition and subtraction operations between duration values and between
        duration/datetime value pairs, and can be the result of subtracting datetime values.

        The tuple must include all values with a zero as a placeholder for unused positions.
        (yyyy,mm,dd,hh,MM,ss.ss) all members are integers except the seconds (last member) being a decimal.
        Example: 2 years, 10 days and 2 hours = (2,0,10,2,0,0).
        Use these values in conjunction with the relativedelta type from the python-dateutil pkg.
        """
        return self._duration

    @duration.setter
    def duration(self, v):
        if self.published:
            if isinstance(v, type(None)):
                self._duration = v
            elif isinstance(v, tuple) and len(v) == 6:
                if all(isinstance(n, int) for n in v[0:4]) and checkers.is_decimal(v[5]):
                    self._duration = v
                else:
                    raise ValueError("Some members of the duration tuple are not the correct type.")
            else:
                raise ValueError("The duration value must be a 6 member tuple (yyyy,mm,dd,hh,MM,ss.ss) of integers except the seconds (last member) being a decimal.")
        else:
            raise PublicationError("The model has not been published.")

    def validate(self):
        """
        Every XdType must implement this method.
        """
        if not super(XdTemporalType, self).validate():
            return(False)
        else:
            return(True)

    def getModel(self):
        """
        Return a XML Schema complexType definition.
        """
        self.validate()
        indent = 2
        padding = ('').rjust(indent)

        xdstr = super().getModel()

        # XdTemporal - every element must be included as either allowed or not allowed.

        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='" + str(self.cardinality['date'][1]) + "' minOccurs='" + str(self.cardinality['date'][0]) + "' name='xdtemporal-date' type='xs:date'/>\n")
        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='" + str(self.cardinality['time'][1]) + "' minOccurs='" + str(self.cardinality['time'][0]) + "' name='xdtemporal-time' type='xs:time'/>\n")
        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='" + str(self.cardinality['datetime'][1]) + "' minOccurs='" + str(self.cardinality['datetime'][0]) + "' name='xdtemporal-datetime' type='xs:dateTime'/>\n")
        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='" + str(self.cardinality['day'][1]) + "' minOccurs='" + str(self.cardinality['day'][0]) + "' name='xdtemporal-day' type='xs:gDay'/>\n")
        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='" + str(self.cardinality['month'][1]) + "' minOccurs='" + str(self.cardinality['month'][0]) + "' name='xdtemporal-month' type='xs:gMonth'/>\n")
        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='" + str(self.cardinality['year'][1]) + "' minOccurs='" + str(self.cardinality['year'][0]) + "' name='xdtemporal-year' type='xs:gYear'/>\n")
        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='" + str(self.cardinality['year_month'][1]) + "' minOccurs='" + str(self.cardinality['year_month'][0]) + "' name='xdtemporal-year-month' type='xs:gYearMonth'/>\n")
        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='" + str(self.cardinality['month_day'][1]) + "' minOccurs='" + str(self.cardinality['month_day'][0]) + "' name='xdtemporal-month-day' type='xs:gMonthDay'/>\n")
        xdstr += padding.rjust(indent + 8) + ("<xs:element maxOccurs='" + str(self.cardinality['duration'][1]) + "' minOccurs='" + str(self.cardinality['duration'][0]) + "' name='xdtemporal-duration' type='xs:duration'/>\n")
        xdstr += padding.rjust(indent + 8) + ("</xs:sequence>\n")
        xdstr += padding.rjust(indent + 6) + ("</xs:restriction>\n")
        xdstr += padding.rjust(indent + 4) + ("</xs:complexContent>\n")
        xdstr += padding.rjust(indent + 2) + ("</xs:complexType>\n\n")

        return(xdstr)

    def getXMLInstance(self, example=False):
        """
        Return an XML fragment for this model.
        """
        if example:
            if not self.published:
                raise PublicationError("Cannot create an example unless the model is published.")
            dt = datetime.now()
            self.date = date.today()
            self.time = datetime.time(dt)
            self.datetime = dt
            self.day = self.date.day
            self.month = self.date.month
            self.year = self.date.year
            self.year_month = (self.date.year,self.date.month)
            self.month_day = (self.date.month,self.date.day)
            # Build a duration
            start = datetime.strptime('1/1/1970', '%m/%d/%Y')
            end = datetime.strptime('12/31/2030', '%m/%d/%Y')
            rdt = start + timedelta(seconds=randint(0, int((end - start).total_seconds())))
            rdt2 = start + timedelta(seconds=randint(0, int((end - start).total_seconds())))
            dur = abs((rdt - rdt2).days)

        indent = 2
        padding = ('').rjust(indent)
        xmlstr = super().getXMLInstance(example)

        if self.cardinality['date'][1] == 1 and self.date is not None:
            xmlstr += padding + """  <xdtemporal-date>""" + datetime.strftime(self.date, '%Y-%m-%d') + """</xdtemporal-date>\n"""
        if self.cardinality['time'][1] == 1 and self.time is not None:
            xmlstr += padding + """  <xdtemporal-time>""" + datetime.strftime(self.time, '%H:%M:%S') + """</xdtemporal-time>\n"""
        if self.cardinality['datetime'][1] == 1 and self.datetime is not None:
            xmlstr += padding + """  <xdtemporal-datetime>""" + datetime.strftime(self.datetime, '%Y-%m-%dT%H:%M:%S') + """</xdtemporal-datetime>\n"""
        if self.cardinality['day'][1] == 1 and self.day is not None:
            xmlstr += padding + """  <xdtemporal-day>---""" + str(self.day) + """</xdtemporal-day>\n"""
        if self.cardinality['month'][1] == 1 and self.month is not None:
            xmlstr += padding + """  <xdtemporal-month>--""" + str(self.month) + """</xdtemporal-month>\n"""
        if self.cardinality['year'][1] == 1 and self.year is not None:
            xmlstr += padding + """  <xdtemporal-year>""" + str(self.year) + """</xdtemporal-year>\n"""
        if self.cardinality['year_month'][1] == 1 and self.year_month is not None:
            xmlstr += padding + """  <xdtemporal-year-month>""" + str(self.year_month[0]) + '-' + str(self.year_month[1]) + """</xdtemporal-year-month>\n"""
        if self.cardinality['month_day'][1] == 1 and self.month_day is not None:
            xmlstr += padding + """  <xdtemporal-month-day>--""" + str(self.month_day[0]) + '-' + str(self.month_day[1]) + """</xdtemporal-month-day>\n"""
        if self.cardinality['duration'][1] == 1 and self.duration is not None:
            xmlstr += padding + """  <xdtemporal-duration>""" + 'P' + ''.join(map(str, self.duration)) + 'D' + """</xdtemporal-duration>\n"""
        xmlstr += padding + """</s3m:ms-""" + str(self.mcuid) + """>\n"""
        if self.adapter:
            xmlstr += padding.rjust(indent) + '</s3m:ms-' + self.acuid + '>\n'

        return(xmlstr)
