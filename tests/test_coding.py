from typing import Literal

from pydantic import TypeAdapter

from fhir_slicing.base import BaseModel
from fhir_slicing.coding import BaseCoding, BaseCodingArray, GeneralCoding, LOINCCoding, SCTCoding
from fhir_slicing.slice import OptionalSlice, Slice, SliceList, slice


def test_multi_coding_concepts():
    class CodingArray(BaseCodingArray):
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


def test_task_code():
    class AtticusTaskType(BaseCoding):
        code: Literal["complete-questionnaire", "process-response"]
        system: Literal["https://tiro.health/fhir/CodeSystem/atticus-task-type"]

    class TaskCodingArray(BaseCodingArray[GeneralCoding | AtticusTaskType]):
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
