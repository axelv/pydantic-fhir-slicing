from typing import Annotated, List, Optional

import pytest

from fhir_slicing.utils import (
    get_source_type,
)


@pytest.mark.parametrize(
    "source, target",
    [
        (Optional[str], (str,)),
        (List[str], (str,)),
        (str, (str,)),
        (List[str] | None, (str,)),
        (Annotated[List[str], "some annotation"], (str,)),
        (Annotated[List[str] | None, "some annotation"], (str,)),
        (Annotated[List[str | int] | None, "some annotation"], (str, int)),
    ],
)
def test_get_source_type(source, target):
    source_types = tuple(get_source_type(source))
    assert source_types == target


class Base:
    pass


class A(Base):
    pass


class B(Base):
    pass


class C:
    pass


@pytest.mark.parametrize(
    "source, expected, raises",
    [
        [A, Base, None],
        [B, Base, None],
        [C, Base, TypeError],
        [A | None, Base, None],
        [B | None, Base, None],
        [C | None, Base, TypeError],
        [Optional[A], Base, None],
        [Optional[B], Base, None],
        [Optional[C], Base, TypeError],
        [List[A], Base, None],
        [List[B], Base, None],
        [List[C], Base, TypeError],
        [List[A | B], Base, None],
        [List[B | C], Base, TypeError],
        [List[A | B] | None, Base, None],
        [List[A | B] | None | None, Base, None],
        [Annotated[List[A | B] | None, "some annotation"], Base, None],
        [Annotated[List[A | C] | None, "some annotation"], Base, TypeError],
    ],
)
def test_get_source_type_with_expect(source, expected, raises):
    source_types_iter = get_source_type(source, expect=expected)
    if raises:
        with pytest.raises(raises):
            tuple(source_types_iter)
    else:
        tuple(source_types_iter)
