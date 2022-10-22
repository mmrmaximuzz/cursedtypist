"""Frontend subpackage for cursedtypist game."""

from abc import ABC, abstractmethod


class Frontend(ABC):
    """Base class for all the frontends in cursedtypist."""

    @abstractmethod
    def run(self, text: str) -> None:
        """Start a game using this frontend and text provided."""
