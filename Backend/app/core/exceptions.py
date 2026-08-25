"""Domain exceptions raised by the service layer.

Deliberately free of FastAPI imports so services never depend on the web
framework: `app.main` owns the mapping from these to HTTP status codes.

None of these carry provider request details. An exception message here can end
up in a log line, and the upstream request URL would otherwise be a place an
API key could leak.
"""


class AmpPilotError(Exception):
    """Base class for errors raised by AmpPilot's own service layer."""


class UpstreamError(AmpPilotError):
    """An upstream data provider failed, or answered with something unusable.

    Covers transport failures, non-success status codes, and malformed bodies.
    Maps to HTTP 502.
    """


class UpstreamTimeout(UpstreamError):
    """An upstream data provider did not answer within the configured timeout.

    Maps to HTTP 504. Subclasses `UpstreamError` so a caller that only cares
    about "upstream broke" can catch the parent.
    """


class UpstreamNotConfigured(AmpPilotError):
    """A required provider credential is missing from the configuration.

    Maps to HTTP 503: the service is deployed but cannot do its job, which is
    an operator problem rather than a caller problem.
    """
