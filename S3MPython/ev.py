"""
Exceptional Values

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


class ExceptionalValue(ABC):
    """
    Subtypes are used to indicate why a value is missing (Null) or is outside a measurable range.
    The element ev-name is fixed in restricted types to a descriptive string. The subtypes defined in the reference model
    are considered sufficiently generic to be useful in many instances.
    Data Models may contain additional ExceptionalValueType restrictions to allow for domain related reasons for
    errant or missing data.
    """

    @abstractmethod
    def __init__(self):
        self._ev_name = ''

    @property
    def ev_name(self):
        """
        A short title or phase for the exceptional type value.
        """
        return self._ev_name

    def __str__(self):
        return(self.__class__.__name__ + ' : ' + self._ev_name)


class NIType(ExceptionalValue):
    """
    No Information : The value is exceptional (missing, omitted, incomplete, improper).
    No information as to the reason for being an exceptional value is provided.
    This is the most general exceptional value. It is also the default exceptional value implemented in tools.
    """

    def __init__(self):
        self._ev_name = 'No Information'


class MSKType(ExceptionalValue):
    """
    Masked : There is information on this item available but it has not been provided by the sender due to security,
    privacy or other reasons. There may be an alternate mechanism for gaining access to this information.
    Warning: Using this exceptional value does provide information that may be a breach of confidentiality,
    even though no detail data is provided. Its primary purpose is for those circumstances where it is necessary to
    inform the receiver that the information does exist without providing any detail.
    """

    def __init__(self):
        self._ev_name = 'Masked'


class INVType(ExceptionalValue):
    """
    Invalid : The value as represented in the instance is not a member of the set of permitted data values in the
    constrained value domain of a variable.
    """

    def __init__(self):
        self._ev_name = 'Invalid'


class DERType(ExceptionalValue):
    """
    Derived : An actual value may exist, but it must be derived from the provided information;
    usually an expression is provided directly.
    """

    def __init__(self):
        self._ev_name = 'Derived'


class UNCType(ExceptionalValue):
    """
    Unencoded : No attempt has been made to encode the information correctly but the raw source information is represented, usually in free text.
    """

    def __init__(self):
        self._ev_name = 'Unencoded'


class OTHType(ExceptionalValue):
    """
    Other: The actual value is not a member of the permitted data values in the variable.
    (e.g., when the value of the variable is not by the coding system)
    """

    def __init__(self):
        self._ev_name = 'Other'


class NINFType(ExceptionalValue):
    """
    Negative Infinity : Negative infinity of numbers
    """

    def __init__(self):
        self._ev_name = 'Negative Infinity'


class PINFType(ExceptionalValue):
    """
    Positive Infinity : Positive infinity of numbers
    """

    def __init__(self):
        self._ev_name = 'Positive Infinity'


class UNKType(ExceptionalValue):
    """
    Unknown : A proper value is applicable, but not known.
    """

    def __init__(self):
        self._ev_name = 'Unknown'


class ASKRType(ExceptionalValue):
    """
    Asked and Refused : Information was sought but refused to be provided (e.g., patient was asked but refused to answer).
    """

    def __init__(self):
        self._ev_name = 'Asked and Refused'


class NASKType(ExceptionalValue):
    """
    Not Asked : This information has not been sought (e.g., patient was not asked)
    """

    def __init__(self):
        self._ev_name = 'Not Asked'


class QSType(ExceptionalValue):
    """
    Sufficient Quantity : The specific quantity is not known, but is known to non-zero and it is not specified because it makes up the bulk of the material;
    Add 10mg of ingredient X, 50mg of ingredient Y and sufficient quantity of water to 100mL.
    """

    def __init__(self):
        self._ev_name = 'Sufficient Quantity'


class TRCType(ExceptionalValue):
    """
    Trace : The content is greater or less than zero but too small to be quantified.
    """

    def __init__(self):
        self._ev_name = 'Trace'


class ASKUType(ExceptionalValue):
    """
    Asked but Unknown : Information was sought but not found (e.g., patient was asked but did not know)
    """

    def __init__(self):
        self._ev_name = 'Asked but Unknown'


class NAVType(ExceptionalValue):
    """
    Not Available: This information is not available and the specific reason is not known.
    """

    def __init__(self):
        self._ev_name = 'Not Available'


class NAType(ExceptionalValue):
    """
    Not Applicable : No proper value is applicable in this context e.g.,the number of cigarettes smoked per day by a non-smoker subject.
    """

    def __init__(self):
        self._ev_name = 'Not Applicable'

