from typing import Generic, Literal, TypeVar

import pytest
from pydantic import TypeAdapter
from pydantic_core import ValidationError

from fhir_slicing.base import BaseModel
from fhir_slicing.coding import BaseCoding, GeneralCoding, LOINCCoding, SCTCoding
from fhir_slicing.element_array import BaseElementArray
from fhir_slicing.slice import OptionalSlice, Slice, SliceList, slice


def test_multi_coding_concepts():
    class CodingArray(BaseElementArray):
        sct: Slice[SCTCoding] = slice(1, 1)
        loinc: OptionalSlice[LOINCCoding] = slice(0, 1)
        _: SliceList[GeneralCoding] = slice(0, "*")

    class CodeableConcept(BaseModel):
        coding: CodingArray
        text: str | None = None

    raw_concept = {
        "coding": [
            {"system": "http://snomed.info/sct", "code": "123456", "display": "Test"},
            {"system": "http://loinc.org", "code": "123456", "display": "Test"},
            {"system": "http://other.org", "code": "123456", "display": "Test"},
        ],
        "text": "Test",
    }

    concept = CodeableConcept.model_validate(raw_concept)

    assert concept.coding.sct.system == "http://snomed.info/sct"
    assert concept.coding.loinc is not None, "Expected loinc to be present"
    assert concept.coding.loinc.system == "http://loinc.org"

    assert (
        concept.model_dump(by_alias=True, exclude_none=True) == raw_concept
    ), "Expected model_dump to match raw_concept"


def test_coding_cardinality_max_items():
    class CodingArray(BaseElementArray):
        sct: Slice[SCTCoding] = slice(1, 1)
        loinc: SliceList[LOINCCoding] = slice(1, 10)
        _: SliceList[GeneralCoding] = slice(0, "*")

    class CodeableConcept(BaseModel):
        coding: CodingArray
        text: str | None = None

    raw_concept = {
        "coding": [
            {"system": "http://loinc.org", "code": "123456", "display": "Test"},
            {"system": "http://snomed.info/sct", "code": "123456", "display": "Test"},
            {"system": "http://snomed.info/sct", "code": "987654", "display": "Test2"},
            {"system": "http://other.org", "code": "123456", "display": "Test"},
        ],
        "text": "Test",
    }
    with pytest.raises(ValidationError) as exc_info:
        CodeableConcept.model_validate(raw_concept)
    error_msgs = [error["msg"] for error in exc_info.value.errors()]
    assert "Value error, Too many items in slice 'sct'" in error_msgs


def test_coding_cardinality_mmin_items():
    class CodingArray(BaseElementArray):
        sct: Slice[SCTCoding] = slice(1, 1)
        loinc: SliceList[LOINCCoding] = slice(2, 10)
        _: SliceList[GeneralCoding] = slice(0, "*")

    class CodeableConcept(BaseModel):
        coding: CodingArray
        text: str | None = None

    raw_concept = {
        "coding": [
            {"system": "http://loinc.org", "code": "123456", "display": "Test"},
            {"system": "http://snomed.info/sct", "code": "987654", "display": "Test2"},
            {"system": "http://other.org", "code": "123456", "display": "Test"},
        ],
        "text": "Test",
    }
    with pytest.raises(ValidationError) as exc_info:
        CodeableConcept.model_validate(raw_concept)
    error_msgs = [error["msg"] for error in exc_info.value.errors()]
    assert "Value error, Not enough items in slice 'loinc'" in error_msgs


def test_task_code():
    class AtticusTaskType(BaseCoding):
        code: Literal["complete-questionnaire", "process-response"]
        system: Literal["https://tiro.health/fhir/CodeSystem/atticus-task-type"]

    class TaskCodingArray(BaseElementArray[GeneralCoding | AtticusTaskType]):
        atticus_task_type: Slice[AtticusTaskType] = slice(1, 1)
        _: SliceList[GeneralCoding] = slice(0, "*")

    coding_array = TaskCodingArray(
        [AtticusTaskType(code="complete-questionnaire", system="https://tiro.health/fhir/CodeSystem/atticus-task-type")]
    )

    coding_array_json = TypeAdapter[TaskCodingArray](TaskCodingArray).dump_python(
        coding_array, by_alias=True, exclude_none=True
    )

    assert coding_array_json == [
        {"system": "https://tiro.health/fhir/CodeSystem/atticus-task-type", "code": "complete-questionnaire"}
    ]


def test_slice_order_in_union():
    class MyCoding[TCode: str](BaseModel):
        code: TCode
        system: Literal["http://mycode.org"]
        display: str

    class CodingArray[TCode: str](BaseElementArray):
        sct: Slice[SCTCoding] = slice(1, 1)
        loinc: SliceList[LOINCCoding] = slice(1, 10)
        _: SliceList[GeneralCoding] = slice(0, "*")
        my: Slice[MyCoding[TCode]] = slice(1, 1)

    result = TypeAdapter(CodingArray).validate_python(
        [
            {"system": "http://snomed.info/sct", "code": "987654", "display": "Test2"},
            {"system": "http://loinc.org", "code": "123456", "display": "Test"},
            {"system": "http://mycode.org", "code": "123456", "display": "Test"},
            {"system": "http://other.org", "code": "123456", "display": "Test"},
        ],
    )

    assert result == [
        SCTCoding(system="http://snomed.info/sct", code="987654", display="Test2"),
        LOINCCoding(system="http://loinc.org", code="123456", display="Test"),
        MyCoding(system="http://mycode.org", code="123456", display="Test"),
        GeneralCoding(system="http://other.org", code="123456", display="Test"),
    ]


TCode = TypeVar("TCode", bound=str)


class MyCoding(BaseModel, Generic[TCode]):
    system: Literal["http://mycode.org"]
    code: TCode
    display: str


class MyCodingArray(BaseElementArray, Generic[TCode]):
    my: Slice[MyCoding[TCode]] = slice(1, 1)
    _: SliceList[GeneralCoding] = slice(0, "*")


def test_generic_coding_array():
    with pytest.raises(ValidationError):
        TypeAdapter(MyCodingArray[Literal["AAAA"]]).validate_python(
            [
                {"system": "http://mycode.org", "code": "123456", "display": "Test"},
                {"system": "http://other.org", "code": "123456", "display": "Test"},
            ],
        )
