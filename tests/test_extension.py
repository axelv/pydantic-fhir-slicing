from typing import Literal

from pydantic import PositiveInt, TypeAdapter

from fhir_slicing import BaseModel, Slice, SliceList, slice
from fhir_slicing.element_array import BaseElementArray
from fhir_slicing.extension import (
    BaseSimpleExtension,
    GeneralExtension,
)


def test_extension_model_get_url():
    class MyExtension(BaseSimpleExtension[Literal["http://example.com"], str]):
        valueString: str

    assert MyExtension.get_url() == "http://example.com"


def test_extension_array_from_extension_list():
    class MyExtensionA(BaseSimpleExtension[Literal["http://example.com/extension-a"], str]):
        valueString: str

    class MyExtensionB(BaseSimpleExtension[Literal["http://example.com/extension-b"], str]):
        valueString: str

    class ExtensionArray(BaseElementArray):
        a: SliceList[MyExtensionA] = slice(0, "*")
        b: Slice[MyExtensionB] = slice(1, 1)
        _: SliceList[GeneralExtension] = slice(0, "*")

    ext_list = [
        MyExtensionA(url="http://example.com/extension-a", valueString="a"),
        MyExtensionA(url="http://example.com/extension-a", valueString="a"),
        MyExtensionA(url="http://example.com/extension-a", valueString="a"),
        MyExtensionB(url="http://example.com/extension-b", valueString="b"),
        GeneralExtension.model_validate({"url": "http://example.com", "valueInteger": 3}),
    ]

    ext_array = ExtensionArray(ext_list)
    assert ext_array.a == ext_list[:3]
    assert ext_array.b == ext_list[3]
    assert list(ext_array) == ext_list


def test_extension_array_validator():
    class MyExtensionA(BaseSimpleExtension[Literal["http://example.com/extension-a"], str]):
        valueString: str

    class MyExtensionB(BaseSimpleExtension[Literal["http://example.com/extension-b"], str]):
        valueString: str

    class ExtensionArray(BaseElementArray):
        a: SliceList[MyExtensionA] = slice(0, "*")
        b: Slice[MyExtensionB] = slice(1, 1)
        _: SliceList[GeneralExtension] = slice(0, "*")

    ext_list = [
        {"url": "http://example.com", "valueInteger": 5},
        {"url": "http://example.com/extension-a", "valueString": "1"},
        {"url": "http://example.com/extension-a", "valueString": "2"},
        {"url": "http://example.com/extension-a", "valueString": "3"},
        {"url": "http://example.com/extension-b", "valueString": "4"},
    ]

    ext_array = TypeAdapter(ExtensionArray).validate_python(ext_list)

    assert ext_array.a == [
        MyExtensionA(url="http://example.com/extension-a", valueString="1"),
        MyExtensionA(url="http://example.com/extension-a", valueString="2"),
        MyExtensionA(url="http://example.com/extension-a", valueString="3"),
    ]

    assert ext_array.b == MyExtensionB(url="http://example.com/extension-b", valueString="4")

    ext_list_roundtrip = TypeAdapter(ExtensionArray).dump_python(ext_array, mode="python")
    assert ext_list_roundtrip == ext_list


def test_extension_array_ordering_roundtrip():
    class MyExtensionA(BaseSimpleExtension[Literal["http://example.com/extension-a"], str]):
        valueString: str

    class MyExtensionB(BaseSimpleExtension[Literal["http://example.com/extension-b"], str]):
        valueString: str

    class ExtensionArray(BaseElementArray):
        a: SliceList[MyExtensionA] = slice(0, "*")
        b: Slice[MyExtensionB] = slice(1, 1)

    ext_array = ExtensionArray(
        (
            MyExtensionA(url="http://example.com/extension-a", valueString="a"),
            MyExtensionA(url="http://example.com/extension-a", valueString="a"),
            MyExtensionA(url="http://example.com/extension-a", valueString="a"),
            MyExtensionB(url="http://example.com/extension-b", valueString="b"),
        )
    )

    ext_list = TypeAdapter(ExtensionArray).dump_python(ext_array)

    assert ext_list == [
        {"url": "http://example.com/extension-a", "valueString": "a"},
        {"url": "http://example.com/extension-a", "valueString": "a"},
        {"url": "http://example.com/extension-a", "valueString": "a"},
        {"url": "http://example.com/extension-b", "valueString": "b"},
    ]

    ext_array_roundtrip = TypeAdapter(ExtensionArray).validate_python(ext_list)

    assert ext_array_roundtrip == ext_array


def test_patient_use_case():
    class MultipleBirth(
        BaseSimpleExtension[Literal["http://hl7.org/fhir/StructureDefinition/patient-multipleBirth"], PositiveInt]
    ):
        valueInteger: PositiveInt

    class PatientExtensions(BaseElementArray):
        multiple_birth: Slice[MultipleBirth] = slice(1, 1)

    class PatientName(BaseModel):
        text: str
        given: list[str] | None = None
        family: str | None = None
        use: Literal["usual", "official", "temp", "nickname", "anounymous", "old", "maiden"] | None = None

    class Patient(BaseModel):
        extensions: PatientExtensions
        resourceType: Literal["Patient"] = "Patient"
        name: list[PatientName] | None = None

        @property
        def multiple_birth(self):
            return self.extensions.multiple_birth.valueInteger

        @multiple_birth.setter
        def set_multiple_birth(self, value: PositiveInt):
            self.extensions.multiple_birth.valueInteger = value

    patient = Patient.model_validate(
        {
            "resourceType": "Patient",
            "name": [
                {
                    "text": "John Doe",
                    "given": ["John"],
                    "family": "Doe",
                    "use": "official",
                },
            ],
            "extensions": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/patient-multipleBirth",
                    "valueInteger": 3,
                }
            ],
        }
    )

    assert patient.extensions.multiple_birth.valueInteger == 3
    assert patient.multiple_birth == 3


def test_extension_array_with_subclassing():
    class MyExtensionA(BaseSimpleExtension[Literal["http://example.com/extension-a"], str]):
        valueString: str

    class MyExtensionB(BaseSimpleExtension[Literal["http://example.com/extension-b"], str]):
        valueString: str

    class ExtensionArray(BaseElementArray):
        a: SliceList[MyExtensionA] = slice(0, "*")
        _: SliceList[GeneralExtension] = slice(0, "*")

    class SubExtensionArray(ExtensionArray):
        b: Slice[MyExtensionB] = slice(1, 1)

    ext_list = [
        {"url": "http://example.com", "valueInteger": 5},
        {"url": "http://example.com/extension-a", "valueString": "1"},
        {"url": "http://example.com/extension-a", "valueString": "2"},
        {"url": "http://example.com/extension-a", "valueString": "3"},
        {"url": "http://example.com/extension-b", "valueString": "4"},
    ]

    ext_array = TypeAdapter(SubExtensionArray).validate_python(ext_list)

    assert ext_array.a == [
        MyExtensionA(url="http://example.com/extension-a", valueString="1"),
        MyExtensionA(url="http://example.com/extension-a", valueString="2"),
        MyExtensionA(url="http://example.com/extension-a", valueString="3"),
    ]

    assert ext_array.b == MyExtensionB(url="http://example.com/extension-b", valueString="4")

    ext_list_roundtrip = TypeAdapter(ExtensionArray).dump_python(ext_array, mode="python")
    assert ext_list_roundtrip == ext_list
