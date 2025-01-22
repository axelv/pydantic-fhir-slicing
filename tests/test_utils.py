from typing import Annotated, List, Optional

import pytest

from fhir_slicing.utils import (
    Cardinality,
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


def test_default_values_of_slice():
    assert Cardinality(min_length=0, max_length="*") == Cardinality()


@pytest.mark.parametrize(
    "slice, source, target",
    [
        (Cardinality(0, "*"), [1, 2, 3], [1, 2, 3]),
        (Cardinality(0, 1), [1], 1),
        (Cardinality(0, 1), [], None),
        (Cardinality(1, "*"), [1, 2, 3], [1, 2, 3]),
        (Cardinality(1, "*"), [1], [1]),
        (Cardinality(1, 1), [1], 1),
    ],
)
def test_aggregate_slice_elements(slice: Cardinality, source: list, target: list):
    assert slice.aggregate_elements(source) == target
