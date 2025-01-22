import types
from dataclasses import dataclass
from typing import (
    Annotated,
    Any,
    Iterable,
    Iterator,
    Literal,
    Sequence,
    Union,
    get_args,
    get_origin,
)

from .slice import OptionalSlice, Slice, SliceList


def get_source_type(annot) -> Iterator[type]:
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
        yield annot
        return

    origin = get_origin(annot)
    if origin is None:
        yield annot

    elif origin is Annotated:
        yield from get_source_type(get_args(annot)[0])

    elif origin is list or origin is set:
        yield from get_source_type(get_args(annot)[0])

    elif origin in (SliceList, OptionalSlice, Slice):
        yield from get_source_type(get_args(annot)[0])

    # check for Union or UnionType
    elif origin is Union or isinstance(annot, types.UnionType):
        for arg in get_args(annot):
            if arg is not type(None):
                yield from get_source_type(arg)
    else:
        raise ValueError(f"Cannot determine source type from {annot}")


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


@dataclass
class Cardinality:
    min_length: int = 0
    max_length: int | Literal["*"] = "*"

    def aggregate_elements(self, elements: Iterator[Any] | Iterable[Any]):
        """Map the element array to the expected python type

        when 0..1 -> Optional[<source_type>]
        when 1..1 -> <source_type>
        when 0..* -> Iterator[<source_type>]
        when 1..* -> Iterator[<source_type>]
        """
        match self.min_length, self.max_length:
            case 0, 1:
                return next(iter(elements), None)
            case 1, 1:
                return next(iter(elements))
            case _:
                return [*elements]

    def iterate_elements(self, value: Any):
        """Iterate over the elements"""
        match self.min_length, self.max_length:
            case 0, 1:
                if value is not None:
                    yield value
            case 1, 1:
                yield value
            case 0, "*":
                if value is not None:
                    yield from value
            case 1, "*":
                yield from value

    @classmethod
    def from_metadata(cls, metadata: Sequence[Any]):
        for meta in metadata:
            if isinstance(meta, Cardinality):
                return meta
        return cls()
