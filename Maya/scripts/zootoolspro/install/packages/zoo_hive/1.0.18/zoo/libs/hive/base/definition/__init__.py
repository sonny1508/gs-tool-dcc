"""
Main api access for component data

:todo: allow for special syntax for referencing in definition files eg.  {"include": vchaincomponent}.
:todo: definition validation.
:todo: create a registry of definitions which will allow us to deserialize with more  types.
:todo: better merging of attributes and the dag.
"""

from .compdefinition import *
from .definitionattrs import *
from .definitionlayers import *
from .definitionnodes import *
from .spaceswitch import *
from .exprutils import *

