from pydantic import BaseModel
from typing import List


class Ingredient(BaseModel):
    name: str
    quantity: str


class Step(BaseModel):
    step_number: int
    instruction: str


class Recipe(BaseModel):
    title: str
    estimated_time: str
    difficulty: str
    equipment: List[str]
    ingredients: List[Ingredient]
    steps: List[Step]


class SafetyWarning(BaseModel):
    type: str
    warning: str


class FirstAid(BaseModel):
    situation: str
    response: str


class SafetyAnalysis(BaseModel):
    safety_warnings: List[SafetyWarning]
    first_aid: List[FirstAid]