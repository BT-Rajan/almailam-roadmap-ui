"""Constants shared across the project_service package's submodules.

Deliberately its own leaf module with no imports back into
project_service -- __init__.py re-exports everything from queries.py
(and, as more of project_service gets split out, its future siblings),
so those submodules can't import constants from __init__ without a
circular import. This file has no such dependents, so everyone can
import from here safely.
"""

import logging

ENTITY_TYPE = "PROJECT"

logger = logging.getLogger("app")
