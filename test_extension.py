from dataclasses import dataclass
from typing import Annotated, List, Literal, Sequence

from pydantic import BaseModel, PositiveInt, TypeAdapter

from extension import (
    BaseExtension,
    BaseExtensionArray,
    BaseSimpleExtension,
    GeneralExtension,
)
from utils import Cardinality


def test_extension_model_get_url():
    class MyExtension(BaseSimpleExtension[Literal["http://example.com"]]):
        valueString: str

    assert MyExtension.get_url() == "http://example.com"


def test_extension_array_from_extension_list():
    class MyExtensionA(BaseSimpleExtension[Literal["http://example.com/extension-a"]]):
        valueString: str

    class MyExtensionB(BaseSimpleExtension[Literal["http://example.com/extension-b"]]):
        valueString: str

    @dataclass
    class ExtensionArray(BaseExtensionArray):
        a: Annotated[List[MyExtensionA], Cardinality(0, "*")]
        b: Annotated[MyExtensionB, Cardinality(1, 1)]

        @classmethod
        def from_extension_list(cls, ext_list: Sequence[BaseExtension]):
            return cls.from_element_list(ext_list, discriminator=cls.discriminator)

    ext_list = [
        MyExtensionA(url="http://example.com/extension-a", valueString="a"),
        MyExtensionA(url="http://example.com/extension-a", valueString="a"),
        MyExtensionA(url="http://example.com/extension-a", valueString="a"),
        MyExtensionB(url="http://example.com/extension-b", valueString="b"),
        GeneralExtension.model_validate({"url": "http://example.com", "valueInteger": 3}),
    ]

    ext_array = ExtensionArray.from_extension_list(ext_list)

    assert ext_array.a == ext_list[:3]
    assert ext_array.b == ext_list[3]
    assert ext_array.other == [ext_list[4]]


def test_extension_array_validator():
    class MyExtensionA(BaseSimpleExtension[Literal["http://example.com/extension-a"]]):
        valueString: str

    class MyExtensionB(BaseSimpleExtension[Literal["http://example.com/extension-b"]]):
        valueString: str

    @dataclass
    class ExtensionArray(BaseExtensionArray):
        a: Annotated[List[MyExtensionA], Cardinality(0, "*")]
        b: Annotated[MyExtensionB, Cardinality(1, 1)]

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

    assert ext_array.other == [GeneralExtension.model_validate({"url": "http://example.com", "valueInteger": 5})]

    ext_list_roundtrip = TypeAdapter(ExtensionArray).dump_python(ext_array, mode="python")
    assert ext_list_roundtrip == ext_list


def test_extension_array_ordering_roundtrip():
    class MyExtensionA(BaseSimpleExtension[Literal["http://example.com/extension-a"]]):
        valueString: str

    class MyExtensionB(BaseSimpleExtension[Literal["http://example.com/extension-b"]]):
        valueString: str

    @dataclass
    class ExtensionArray(BaseExtensionArray):
        a: Annotated[List[MyExtensionA], Cardinality(0, "*")]
        b: Annotated[MyExtensionB, Cardinality(1, 1)]

    ext_array = ExtensionArray(
        a=[
            MyExtensionA(url="http://example.com/extension-a", valueString="a"),
            MyExtensionA(url="http://example.com/extension-a", valueString="a"),
            MyExtensionA(url="http://example.com/extension-a", valueString="a"),
        ],
        b=MyExtensionB(url="http://example.com/extension-b", valueString="b"),
    )

    ext_list = TypeAdapter(ExtensionArray).validate_python(ext_array)

    assert ext_list == [
        {"url": "http://example.com/extension-a", "valueString": "a"},
        {"url": "http://example.com/extension-a", "valueString": "a"},
        {"url": "http://example.com/extension-a", "valueString": "a"},
        {"url": "http://example.com/extension-b", "valueString": "b"},
    ]

    ext_array_roundtrip = TypeAdapter(ExtensionArray).validate_python(ext_list)

    assert ext_array_roundtrip == ext_array


def test_patient_use_case():
    class MultipleBirth(BaseSimpleExtension[Literal["http://hl7.org/fhir/StructureDefinition/patient-multipleBirth"]]):
        valueInteger: PositiveInt

    @dataclass
    class PatientExtensions(BaseExtensionArray):
        multiple_birth: Annotated[MultipleBirth, Cardinality(1, 1)]

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
        def multiple_birth(self, value: PositiveInt):
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
