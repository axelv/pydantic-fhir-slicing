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
def get_source_type[T](annot, expect: Type[T]) -> Iterator[Type[T]]: ...
@overload
def get_source_type[T](annot, expect: None = None) -> Iterator[type]: ...
def get_source_type[T](annot, expect: Type[T] | None = None) -> Iterator[type | Type[T]]:
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
    # If the annotation is a type, return the type
    if isinstance(annot, type):
        if expect is not None:
            if not issubclass(annot, expect):
                raise TypeError(f"Expected type to be a subclass of {expect}, got {annot}")
        yield annot
        return

    origin = get_origin(annot)
    if origin is None:
        yield annot

    elif origin is Annotated:
        yield from get_source_type(get_args(annot)[0], expect=expect)

    elif origin is list or origin is set:
        yield from get_source_type(get_args(annot)[0], expect=expect)

    elif origin in (SliceList, OptionalSlice, Slice):
        yield from get_source_type(get_args(annot)[0], expect=expect)

    # check for Union or UnionType
    elif origin is Union or isinstance(annot, types.UnionType):
        for arg in get_args(annot):
            if arg is not type(None):
                yield from get_source_type(arg, expect=expect)
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
