from typing import Protocol


class Payload(Protocol):
    """
    Defines the contract for message payload objects.

    Payload objects encapsulate the data required by message
    handlers to process a specific message type.

    Implementations must provide a serializable representation
    so the payload can be persisted and reconstructed when
    the message is processed.
    """

    def to_dict(self) -> dict:
        """
        Converts the payload into a serializable dictionary.

        Returns:
            dict:
                Serialized payload data used during message
                persistence and processing.
        """
        ...
