import types
from typing import (
    Annotated,
    Iterator,
    Literal,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    overload,
)

from .slice import OptionalSlice, Slice, SliceList

T = TypeVar("T")


@overload
def get_source_type[T](annot, *, expect: Type[T], type_map: dict[TypeVar, type]) -> Iterator[Type[T]]: ...
@overload
def get_source_type[T](annot, *, expect: None = None, type_map: dict[TypeVar, type]) -> Iterator[type]: ...
def get_source_type[T](
    annot, *, expect: Type[T] | None = None, type_map: dict[TypeVar, type]
) -> Iterator[type | Type[T]]:
    """Extract the source type from a optional type or sequence type

    Example:
        get_source_type(Optional[str]) -> str
        get_source_type(List[str]) -> str
        get_source_type(str) -> str
        get_source_type(List[str]|None) -> str
        get_source_type(Annotated[str, "some annotation"]) -> str
        get_source_type(Annotated[List[str], "some annotation"]) -> str
        get_source_type(Annotated[List[str]|None, "some annotation"]) -> str
        get_source_type(Annotated[List[str|int]|None, "some annotateion"]) --> str, int
    """

    origin = get_origin(annot)
    if origin is None:
        substituted_type = substitute_type_parameter(annot, type_map=type_map)
        if expect is not None:
            if not issubclass(substituted_type, expect):
                raise TypeError(f"Expected type to be a subclass of {expect}, got {substituted_type}")
        yield substituted_type

    elif origin is Annotated:
        yield from get_source_type(get_args(annot)[0], expect=expect, type_map=type_map)

    elif origin is list or origin is set:
        yield from get_source_type(get_args(annot)[0], expect=expect, type_map=type_map)

    elif origin in (SliceList, OptionalSlice, Slice):
        yield from get_source_type(get_args(annot)[0], expect=expect, type_map=type_map)

    # check for Union or UnionType
    elif origin is Union or isinstance(annot, types.UnionType):
        for arg in get_args(annot):
            if arg is not type(None):
                yield from get_source_type(arg, expect=expect, type_map=type_map)
    else:
        raise ValueError(f"Cannot determine source type from {annot}")


def get_value_from_literal(literal: type | None) -> int | str | None:
    """Get the value from a Literal type"""
    if get_origin(literal) is not Literal:
        return None
    return get_args(literal)[0]


# All FHIR Data Types
FHIRType = Literal[
    # Primitive Types
    "base64Binary",
    "boolean",
    "canonical",
    "code",
    "date",
    "dateTime",
    "decimal",
    "id",
    "instant",
    "integer",
    "integer64",
    "markdown",
    "oid",
    "positiveInt",
    "string",
    "time",
    "unsignedInt",
    "uri",
    "url",
    "uuid",
    # Complex Types
    "Address",
    "Age",
    "Annotation",
    "Attachment",
    "CodeableConcept",
    "CodeableReference",
    "Coding",
    "ContactPoint",
    "Count",
    "Distance",
    "Duration",
    "HumanName",
    "Identifier",
    "Money",
    "Period",
    "Quantity",
    "Range",
    "Ratio",
    "RatioRange",
    "Reference",
    "SampledData",
    "Signature",
    "Timing",
    # Metadata Types
    "ContactDetail",
    "DataRequirement",
    "Expression",
    "ExtendedContactDetail",
    "ParameterDefinition",
    "RelatedArtifact",
    "TriggerDefinition",
    "UsageContext",
    "Availability",
    # Special Types
    "Dosage",
    "Element",
    "Extension",
    "Meta",
    "Narrative",
]


def get_type_parameter_map(cls, source_type):
    """Return a mapping of type parameters (≈ TypeVar's in Generics) to their corresponding types."""
    type_params = cls.__parameters__
    type_args = get_args(source_type)
    type_parameter_map = dict(zip(type_params, type_args))
    return type_parameter_map


def substitute_type_parameter(t: TypeVar | type, type_map: dict[TypeVar, type]):
    origin = get_origin(t)
    if origin is not None:
        old_args = get_args(t)
        new_args = tuple(substitute_type_parameter(arg, type_map) for arg in old_args)
        return origin[new_args]
    type_parameters = getattr(t, "__parameters__", None)
    if type_parameters is not None and len(type_parameters) > 0:
        new_args = tuple(substitute_type_parameter(arg, type_map) for arg in type_parameters)
        return t[new_args]  # type: ignore[type]

    return type_map.get(t, t)  # type: ignore[type]
