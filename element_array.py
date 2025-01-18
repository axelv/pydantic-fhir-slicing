from abc import abstractmethod
from dataclasses import dataclass, fields
from functools import partial
from itertools import groupby
from typing import (
    Annotated,
    Any,
    Callable,
    Collection,
    Iterator,
    Literal,
    LiteralString,
    Self,
    Sequence,
    TypeVar,
    get_args,
    get_origin,
)

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from utils import Cardinality, FHIRType, get_source_type

TUrl = TypeVar("TUrl", bound=LiteralString)


TFhirType = TypeVar("TFhirType", bound=FHIRType)
TPythonType = TypeVar("TPythonType")


# resource.extension["itemControl"].valueCodeableConcept.coding["tiro"].code

DiscriminatorType = Literal["value", "exists", "type"]
TBaseElement = TypeVar("TBaseElement")
TOtherElement = TypeVar("TOtherElement")


@dataclass(kw_only=True)
class BaseElementArray[TBaseElement, TOtherElement](Collection[TBaseElement]):
    """A collection of elements that can be sliced and named using a discriminator."""

    other: Annotated[list[TOtherElement] | None, Cardinality(0, "*")] = None

    def __len__(self):
        return sum(len(self.__dict__[field_.name]) for field_ in fields(self))

    def __contains__(self, x: object, /) -> bool:
        for field_ in fields(self):
            if x in self.__dict__[field_.name]:
                return True
        return False

    def __iter__(self) -> Iterator[TBaseElement]:
        for field_ in fields(self):
            yield from self.__dict__[field_.name]

    @classmethod
    def get_schema_for_slices(cls, handler: GetCoreSchemaHandler):
        """Generate a schema for each slice.

        Args:
            handler (GetCoreSchemaHandler): The handler to generate the schema

        Yields:
            tuple[str, CoreSchema]: The name of the slice and the schema
        """
        for field_ in fields(cls):
            source_types = list(get_source_type(field_.type))
            match len(source_types):
                case 0:
                    raise ValueError(f"Expected a source type, got {source_types}")
                case 1:
                    yield field_.name, handler(source_types[0])
                case _:
                    yield field_.name, core_schema.union_schema([handler(source_type) for source_type in source_types])

    @classmethod
    def get_cardinality_for_slices(cls) -> Iterator[tuple[str, Cardinality]]:
        """Get the cardinality for each slice"""
        for field_ in fields(cls):
            metadata = get_args(field_.type)[1:] if get_origin(field_.type) is Annotated else []
            yield field_.name, Cardinality.from_metadata(metadata)

    @classmethod
    @abstractmethod
    def discriminator(cls, value: Any) -> str | None:
        """Get the discriminator value for a given value."""
        ...

    @classmethod
    def from_element_list(
        cls,
        extensions: Sequence[TBaseElement],
        *,
        discriminator: Callable[[TBaseElement], str | None],
    ):
        """Merge the extensions into the slices"""
        # maybe define cached properties instead???
        slice_card_map = dict(cls.get_cardinality_for_slices())
        data = {}
        for field_name, slice_extensions in groupby(extensions, key=discriminator):
            cardinality = slice_card_map[field_name or "other"]
            data[field_name] = cardinality.aggregate_elements(iter(slice_extensions))
        return cls(**data)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler):
        choices: dict[str, CoreSchema] = dict(cls.get_schema_for_slices(handler))
        schema = core_schema.list_schema(
            core_schema.tagged_union_schema(choices=choices, discriminator=cls.discriminator)
        )
        return core_schema.no_info_after_validator_function(
            partial(cls.from_element_list, discriminator=cls.discriminator),
            schema,
            serialization=core_schema.plain_serializer_function_ser_schema(cls.serialize, return_schema=schema),
        )

    @classmethod
    def serialize(cls, x: Self):
        card_map = dict(cls.get_cardinality_for_slices())
        elements = []
        for field_ in fields(cls):
            card = card_map[field_.name]
            elements.extend(card.iterate_elements(getattr(x, field_.name)))
        return elements


if __name__ == "__main__":
    pass
