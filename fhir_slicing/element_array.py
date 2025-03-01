import inspect
from abc import abstractmethod
from typing import (
    Any,
    ClassVar,
    List,
    Literal,
    LiteralString,
    TypeVar,
    get_origin,
)

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from .utils import FHIRType, get_source_type

TUrl = TypeVar("TUrl", bound=LiteralString)
TFhirType = TypeVar("TFhirType", bound=FHIRType)
TPythonType = TypeVar("TPythonType")


# resource.extension["itemControl"].valueCodeableConcept.coding["tiro"].code

DiscriminatorType = Literal["value", "exists", "type"]
TDefaultElement = TypeVar("TDefaultElement")


class BaseElementArray[TDefaultElement](List[TDefaultElement]):
    """A collection of elements that can be sliced and named using a discriminator."""

    @classmethod
    def get_slice_annotations(cls) -> dict[str, type]:
        return {
            slice_name if slice_name != "_" else "@default": slice_type
            for slice_name, slice_type in inspect.get_annotations(cls).items()
            if get_origin(slice_type) is not ClassVar
        }

    @classmethod
    def get_schema_for_slices(cls, handler: GetCoreSchemaHandler):
        """Generate a schema for each slice.

        Args:
            handler (GetCoreSchemaHandler): The handler to generate the schema

        Yields:
            tuple[str, CoreSchema]: The name of the slice and the schema
        """
        for slice_name, slice_type in cls.get_slice_annotations().items():
            source_types = list(get_source_type(slice_type))
            match len(source_types):
                case 0:
                    raise TypeError(f"Expected a source type, got none for {slice_name}")
                case 1:
                    yield slice_name, handler(source_types[0])
                case _:
                    yield slice_name, core_schema.union_schema([handler(source_type) for source_type in source_types])

    @classmethod
    @abstractmethod
    def discriminator(cls, value: Any) -> str | None:
        """Get the discriminator value for a given value."""
        ...

    @classmethod
    def check_slice_annotations(cls):
        """Check the slice annotations.
        This is a general check for slice annotations. Subclass should extend this method
        to provide specific checks for their own slice annotations.
        """
        for slice_name, slice_type in cls.get_slice_annotations().items():
            source_types = list(get_source_type(slice_type))
            if len(source_types) == 0:
                raise TypeError(f"Expected a source type, got {source_types}")

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler):
        """Get the Pydantic core schema for the element array."""
        cls.check_slice_annotations()
        choices: dict[str, CoreSchema] = dict(cls.get_schema_for_slices(handler))
        schema = core_schema.list_schema(
            core_schema.tagged_union_schema(choices=choices, discriminator=cls.discriminator)
        )
        # TODO add after validators for cardinality of each slice
        return core_schema.json_or_python_schema(
            core_schema.no_info_after_validator_function(
                cls,
                schema,
            ),
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    core_schema.no_info_after_validator_function(cls, schema),
                ]
            ),
        )


if __name__ == "__main__":
    pass
