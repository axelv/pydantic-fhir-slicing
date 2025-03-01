from typing import Annotated, Any, Container, Iterable, List, Literal, Protocol, TypeVar, overload

import annotated_types

TValueType = TypeVar("TValueType", covariant=True)


class ElementArray(Protocol):
    @classmethod
    def discriminator(cls, value: Any) -> str | None:
        """Get the discriminator value for a given value."""
        ...


class BaseSlice:
    def __set_name__(self, owner: ElementArray, name: str):
        self.name = name
        self.discriminator_func = owner.discriminator

    def filter_element(self, element):
        return self.discriminator_func(element) == self.name


class Slice[TValueType](BaseSlice):
    def __get__(self, obj: Iterable, objtype: type[Container] | None = None) -> TValueType:
        try:
            return next(iter(filter(self.filter_element, obj)))
        except StopIteration:
            raise ValueError(f"No value for slice '{self.name}'.")

    def __set__(self, obj: List, value: Any):
        for index, element in enumerate(obj):
            if self.discriminator_func(element) == self.discriminator_func(value):
                obj[index] = value
                return
        raise ValueError("Cannot set value on slice.")


class OptionalSlice[TValueType](BaseSlice):
    def __get__(self, obj: Iterable, objtype: type[Container] | None = None) -> TValueType | None:
        return next(iter(filter(self.filter_element, obj)), None)

    def __set__(self, obj: List, value: Any):
        for index, element in enumerate(obj):
            if self.discriminator_func(element) == self.discriminator_func(value):
                obj[index] = value
                return


class SliceList[TValueType](BaseSlice):
    def __set_name__(self, owner: ElementArray, name: str):
        self.name = name
        self.discriminator_func = owner.discriminator

    def filter_element(self, element):
        return self.discriminator_func(element) == self.name

    def __get__(self, obj: Iterable, objtype: type[Container] | None = None) -> List[TValueType]:
        return [*filter(self.filter_element, obj)]

    def __set__(self, obj: List, value: List):
        raise NotImplementedError("Cannot set value on slice list.")


NonZeroPositiveInt = Annotated[int, annotated_types.Gt(0)]


@overload
def slice(min: Literal[0], max: Literal[1]) -> OptionalSlice: ...
@overload
def slice(min: Literal[1], max: Literal[1]) -> Slice: ...
@overload
def slice(min: NonZeroPositiveInt, max: Literal["*"]) -> SliceList: ...
def slice(min: int, max: int | Literal["*"]):
    match (min, max):
        case (1, 1):
            return Slice()
        case (0, 1):
            return OptionalSlice()
        case (0, "*"):
            return SliceList()
        case _:
            raise ValueError("Invalid slice cardinality.")
