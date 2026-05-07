import uuid
from dataclasses import dataclass, field


@dataclass(slots=True)
class IntegrationEvent:
    """
    Represents an integration message (intent) to be published.
    """

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    type: str = ''
    payload: dict = field(default_factory=dict)
