from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    pass


class EventBus:
    _handlers: dict[type, list] = {}

    @classmethod
    def subscribe(cls, event_type: type, handler) -> None:
        cls._handlers.setdefault(event_type, []).append(handler)

    @classmethod
    async def publish(cls, event: DomainEvent) -> None:
        for handler in cls._handlers.get(type(event), []):
            await handler(event)


event_bus = EventBus()
