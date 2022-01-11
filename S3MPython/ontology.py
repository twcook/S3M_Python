"""
Defines the S3Model ontology in Python 3.7

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
from dataclasses import dataclass

@dataclass
class CMC:
    """
    Core Model Component - A component model contained in a reference model. 
    A CMC represents a specific core type of component that further contains elements with base datatypes and other CMCs to define its structure.</s3m:description>
    """

@dataclass
class CMS:
    """
    Core Model Symbol - A CMS represents a CMC in instance data. 
    In practice, it is usually substituted for by a Replaceable Model Symbol (RMS). 
    This substitution is because constraints are expressed in a Replaceable Model Component (RMC) which is then represented by an RMS.</s3m:description>
    """
    
    