import uuid
from typing import NewType

EntityId = NewType("EntityId", str)


def new_entity_id() -> EntityId:
    return EntityId(str(uuid.uuid4()))
