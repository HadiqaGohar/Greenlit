"""App package initialization.

Ensures third-party library compatibility shims are applied before any
google-genai / aiohttp usage occurs elsewhere in the app.
"""

import aiohttp

# google-genai references `aiohttp.ClientConnectorDNSError` in its aiohttp
# retry/except clauses, but aiohttp >= 3.9 no longer exposes that name at the
# top level. Map it to the still-present base class so the except clauses
# resolve correctly instead of raising AttributeError and masking real
# connection errors during Imagen/API calls.
if not hasattr(aiohttp, "ClientConnectorDNSError"):
    aiohttp.ClientConnectorDNSError = aiohttp.ClientConnectorError
