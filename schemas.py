
"""
schemas.py

Pydantic schemas used throughout the
AI Mock Interviewer application.
"""

from pydantic import BaseModel, Field
from typing import List


# ============================================================
# QUESTION SCHEMA
# ============================================================

class Question(BaseModel):
    """
    Generated interview question.
    """

    question: str = Field(
        description="Interview question"
    )

    topic: str = Field(
        description="Main topic such as Python, SQL, GenAI"
    )

    subtopic: str = Field(
        description="Specific subtopic being tested"
    )

    difficulty: str = Field(
        description="easy, medium, or hard"
    )

    options: List[str] = Field(
        default_factory=list,
        description="Exactly four options labeled A, B, C and D"
    )

    correct_answer: str = Field(
        default="",
        description="Correct answer letter only: A, B, C or D"
    )

    explanation: str = Field(
        default="",
        description="Explanation of why the correct answer is correct"
    )


# ============================================================
# MCQ EVALUATION
# ============================================================

class Evaluation(BaseModel):
    """
    Evaluation of MCQ answers.
    """

    score: int = Field(
        description="Score between 0 and 10"
    )

    is_correct: bool = Field(
        description="Whether the answer is correct"
    )

    feedback: str = Field(
        description="Feedback explaining the result"
    )

    follow_up_topic: str = Field(
        default="",
        description="Recommended topic for improvement"
    )


# ============================================================
# WRITTEN ANSWER EVALUATION
# ============================================================

class WrittenEvaluation(BaseModel):
    """
    Evaluation of written answers.
    """

    score: int = Field(
        description="Score between 0 and 10"
    )

    feedback: str = Field(
        description="Detailed feedback"
    )

    strengths: List[str] = Field(
        description="Strong aspects of the answer"
    )

    weaknesses: List[str] = Field(
        description="Weak aspects of the answer"
    )


# ============================================================
# FINAL REPORT
# ============================================================

class FinalReport(BaseModel):
    """
    Complete interview report.
    """

    overall_score: float = Field(
        description="Overall score out of 10"
    )

    strengths: List[str] = Field(
        description="Topics and subtopics where the candidate performed well"
    )

    weaknesses: List[str] = Field(
        description="Topics and subtopics where the candidate struggled"
    )

    recommendations: List[str] = Field(
        description="Recommended topics to study"
    )

    summary: str = Field(
        description="Overall interview summary"
    )


# ============================================================
# OPTIONAL ANALYTICS SCHEMA
# (useful for future dashboard features)
# ============================================================

class TopicPerformance(BaseModel):
    topic: str
    average_score: float
    questions_attempted: int


class InterviewSession(BaseModel):
    candidate_name: str
    topic: str
    difficulty: str
    overall_score: float
