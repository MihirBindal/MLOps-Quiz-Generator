from pydantic import BaseModel, Field
from pydantic import BaseModel, Field
from typing import List

class QuizQuestion(BaseModel):
    question: str = Field(description="The quiz question string")
    options: list[str] = Field(description="List of 4 possible answers")
    correct_answer: str = Field(description="The correct answer string")
    option_explanations: dict[str, str] = Field(description="Dictionary mapping each option string to its specific explanation")

class QuizResponse(BaseModel):
    questions: List[QuizQuestion] = Field(description="List of generated quiz questions")