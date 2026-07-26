# IMPORTANT: DO NOT REMOVE THIS IMPORT.
# This import is required to load and initialize the FastAPI application.
# Although `app` is not used directly in this module, importing it loads
# the module where the FastAPI application instance is created and configured.
# The import alone is sufficient for the ASGI server to discover and execute
# the FastAPI application.
#
# The `noqa: F401` directive is required when using Ruff because Ruff
# otherwise considers `app` an unused import and may remove it automatically.
from adapters.inputs.api.app import app  # noqa: F401
