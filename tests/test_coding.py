from fhir_slicing.base import BaseModel
from fhir_slicing.coding import BaseCodingArray, GeneralCoding, LOINCCoding, SCTCoding
from fhir_slicing.slice import OptionalSlice, Slice, SliceList, slice


def test_multi_coding_concepts():
    class CodingArray(BaseCodingArray):
        sct: Slice[SCTCoding] = slice(1, 1)
        loinc: OptionalSlice[LOINCCoding] = slice(0, 1)
        _: SliceList[GeneralCoding] = slice(0, "*")

    class CodeableConcept(BaseModel):
        coding: CodingArray
        text: str | None = None

    concept = CodeableConcept.model_validate(
        {
            "coding": [
                {"system": "http://snomed.info/sct", "code": "123456", "display": "Test"},
                {"system": "http://loinc.org", "code": "123456", "display": "Test"},
                {"system": "http://other.org", "code": "123456", "display": "Test"},
            ],
            "text": "Test",
        }
    )

    assert concept.coding.sct.system == "http://snomed.info/sct"
    assert concept.coding.loinc is not None, "Expected loinc to be present"
    assert concept.coding.loinc.system == "http://loinc.org"
