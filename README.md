# 🔪 FHIR Slicing utilities for Pydantic

[![PyPI version](https://badge.fury.io/py/fhir-slicing.svg)](https://badge.fury.io/py/fhir-slicing)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A Python library that simplifies working with nested elements in FHIR resources using Pydantic models and smart slicing.

## 🚀 Installation
```bash
pip install fhir-slicing
```

## 🤔 The Challenge

Working with FHIR resources in Python can be challenging due to their complex structure and extensibility. FHIR resources often contain:
- Nested elements with cardinality `0..*` or `1..*`
- Extension arrays with unknown elements

This leads to verbose and error-prone code when accessing nested data:

```python
# Traditional way to access birth place
birth_place = next(
    (e.valueAddress.city
     for e in patient.extension
     if e.url == "http://hl7.org/fhir/StructureDefinition/patient-birthPlace"),
    None
)
```

```python
# Traditional way to access systolic blood pressure
bp_reading = observation.component[0].valueQuantity.value  # Fragile! Assumes systolic is first
```

```python

# or by code but not very readable
systolic = next(
    (c.valueQuantity.value
     for c in observation.component
     if c.code.coding[0].code == "8480-6"),
    None
)
```

## ✨ Solution: Smart Slicing

This library introduces a __more intuitive way to access nested FHIR data using named slices__, inspired by FHIR's slicing mechanism.

Known slices are defined as annotated fields in Pydantic models, which provide:
- ✅ Validation of slice cardinality
- 🛡️ Type safety for slice elements
- 📖 Improved readability

**Example: Patient with birthPlace extension**

```python
# Access known extensions by name, while preserving access to unknown ones
patient.extension.birthPlace.valueAddress.city
patient.extension[0]  # Still works for accessing any extension

```

**Example: Blood Pressure Observation with systolic and diastolic components**

```python
# Access components naturally
bp = BloodPressureObservation.model_validate(data)
systolic = bp.component.systolic.valueQuantity.value
diastolic = bp.component.diastolic.valueQuantity.value

```
## ❓ How
Setting up your models for slicing is as simple as subclassing `ElementArray` and defining a discriminator method.

> [!NOTE]
> Interested in how it works? Check out [this blog post](./NOTES.md) for more details.
**Example: Patient with birthPlace extension**

```python
from pydantic_fhir_slicing import Slice, ElementArray
from my_fhir_types import Address, BaseModel

class AddressExtension(BaseModel):
    url: str
    valueAddress: Address

class PatientExtensions(ElementArray):
    birthPlace: AddressExtension = Slice(1, 1)

    def discriminator(self, item) -> str:
        url = item.get("url", None)
        match url:
            case "http://hl7.org/fhir/StructureDefinition/patient-birthPlace":
                return "birthPlace"
            case _:
                return "@default"

class Patient(BaseModel):
    extension: PatientExtensions
```

**Example: Blood Pressure Observation with systolic and diastolic components**

```python
from pydantic_fhir_slicing import ElementArray
from my_fhir_types import CodeableConcept, Quantity, BaseModel

class QuantityComponent(BaseModel):
    code: CodeableConcept
    valueQuantity: Quantity

class BPComponents(ElementArray):
    systolic: QuantityComponent = Slice(1, 1)
    diastolic: QuantityComponent = Slice(1, 1)

    def discriminator(self, item: Component) -> str:
        try:
            code = item["code"]["coding"][0]["code"]
            match code:
                case "8480-6":
                    return "systolic"
                case "8462-4":
                    return "diastolic"
                case _:
                    return "@default"
        except (KeyError, IndexError):
            return "@default"

class BloodPressureObservation(BaseModel):
    code: CodeableConcept
    component: BPComponents
```

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

MIT License
