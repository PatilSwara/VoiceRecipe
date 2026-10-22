from typing import Annotated, List

from pydantic import BaseModel, Field, StringConstraints


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Ingredient(BaseModel):
    name: NonEmptyText
    quantity: NonEmptyText


class Step(BaseModel):
    step_number: int
    instruction: NonEmptyText


class Recipe(BaseModel):
    title: NonEmptyText
    estimated_time: NonEmptyText
    difficulty: NonEmptyText
    equipment: List[str]
    ingredients: List[Ingredient] = Field(min_length=1)
    steps: List[Step] = Field(min_length=1)


class SafetyWarning(BaseModel):
    type: NonEmptyText
    warning: NonEmptyText


class FirstAid(BaseModel):
    situation: NonEmptyText
    response: NonEmptyText


class SafetyAnalysis(BaseModel):
    safety_warnings: List[SafetyWarning]
    first_aid: List[FirstAid]
