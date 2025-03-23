import logging
from types import UnionType
from typing import Mapping, Type

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Any

from fhir_slicing.utils import get_source_type, get_value_from_literal

LOGGER = logging.getLogger(__name__)


def check_if_type_is_union_type(type_: Any) -> bool:
    return isinstance(type_, UnionType)


def get_schema_for_slice(handler: GetCoreSchemaHandler, slice_type: type):
    """Generate a schema for each slice.

    Args:
        handler (GetCoreSchemaHandler): The handler to generate the schema

    Yields:
        tuple[str, CoreSchema]: The name of the slice and the schema
    """
    source_types = list(get_source_type(slice_type))
    match len(source_types):
        case 0:
            raise TypeError("Expected a source type, got none")
        case 1:
            yield handler(source_types[0])
        case _:
            yield core_schema.union_schema([handler(source_type) for source_type in source_types])


def get_value_to_slice_name_map[TSliceType](
    slice_annotations: dict[str, Type], slice_type: Type[TSliceType] | None = None
) -> dict[str, str]:
    map = {}
    for slice_name, slice_annotation in slice_annotations.items():
        source_types = list(get_source_type(slice_annotation, expect=slice_type))
        if len(source_types) > 1:
            raise NotImplementedError(f"Slice {slice_name} has multiple source types. This is not supported")
        slice_value = get_value_from_literal(source_types[0])
        if slice_value is None:
            raise TypeError(f"Slice {slice_name} has no value")
        if slice_value in map:
            raise TypeError(f"Slice {slice_name} has duplicate value")
        map[slice_value] = slice_name
    return map


def get_slice_union_with_value_discriminator_schema(
    source_type: UnionType,
    path: str,
    handler: GetCoreSchemaHandler,
    slice_annotations: dict[str, Type],
) -> CoreSchema:
    value_to_slice_name = get_value_to_slice_name_map(slice_annotations)

    def discriminator(value: Any):
        if isinstance(value, Mapping):
            return value_to_slice_name.get(value.get(path, {}), None)
        LOGGER.warning(
            "⚠️Encountered slice type which is not a mapping. Make sure to implement the Mapping protocol on all slice types."
        )
        return None

    choices: dict[str, CoreSchema] = {
        slice_name: slice_schema
        for slice_name, slice_type in slice_annotations.items()
        for slice_schema in get_schema_for_slice(handler, slice_type)
    }

    return core_schema.tagged_union_schema(choices=choices, discriminator=discriminator)


def get_slice_union_schema(
    source_type: UnionType, handler: GetCoreSchemaHandler, slice_annotations: dict[str, Type]
) -> CoreSchema:
    # type hint is necessary for union_schema input

    default_slice_type = slice_annotations.pop("@default", None)

    choices: list[CoreSchema | tuple[CoreSchema, str]] = [
        (slice_schema, slice_name)
        for slice_name, slice_annotation in slice_annotations.items()
        for slice_schema in get_schema_for_slice(handler, slice_annotation)
    ]
    schema = core_schema.union_schema(choices=choices, mode="smart")
    if default_slice_type is not None:
        default_schema = next(get_schema_for_slice(handler, default_slice_type))
        # Make sure all 'defined' slices get priority over the default slice
        schema = core_schema.union_schema(choices=[schema, default_schema], mode="left_to_right")

    return schema
