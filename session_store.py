"""In-memory interview session management."""

import random
import uuid
from dataclasses import dataclass, field
from typing import Any

from chains import (
    answer_chain,
    evaluation_chain,
    question_chain,
    voice_question_chain,
    report_chain,
    written_evaluation_chain,
)
from schemas import Evaluation, FinalReport, Question
from subtopics import SUBTOPICS


@dataclass
class InterviewSession:
    session_id: str
    name: str
    age: int
    experience: str
    topic: str
    difficulty: str
    answer_format: str
    num_questions: int
    current_question: Question | None = None
    questions: list[Question] = field(default_factory=list)
    answers: list[str] = field(default_factory=list)
    evaluations: list[Any] = field(default_factory=list)
    question_history: list[str] = field(default_factory=list)
    question_index: int = 0
    subtopic_index: int = 0
    shuffled_subtopics: list[str] = field(default_factory=list)
    formats_used: list[str] = field(default_factory=list)
    finished: bool = False

    def _initialize_subtopics(self) -> None:
        topic_subtopics = SUBTOPICS.get(self.topic, ["General Concepts"])
        self.shuffled_subtopics = topic_subtopics.copy()
        random.shuffle(self.shuffled_subtopics)

    def _get_next_subtopic(self) -> str:
        if not self.shuffled_subtopics:
            return "General Concepts"
        idx = self.subtopic_index % len(self.shuffled_subtopics)
        return self.shuffled_subtopics[idx]

    def _generate_question(self, is_voice_mode: bool = False) -> Question:
        current_subtopic = self._get_next_subtopic()
        payload = {
            "topic": self.topic,
            "current_subtopic": current_subtopic,
            "difficulty": self.difficulty,
            "experience": self.experience,
            "history": self.question_history,
        }
        if is_voice_mode:
            return voice_question_chain.invoke(payload)
        return question_chain.invoke(payload)

    def get_current_format(self) -> str:
        total_answered = len(self.questions)
        if self.answer_format == "Combined":
            return "MCQ" if total_answered % 2 == 0 else "Written"
        return self.answer_format

    def start(self, is_voice_mode: bool = False) -> Question:
        self._initialize_subtopics()
        self.current_question = self._generate_question(is_voice_mode=is_voice_mode)
        return self.current_question

    def submit_answer(self, answer: str, is_voice_mode: bool = False) -> dict:
        if self.finished or self.current_question is None:
            raise ValueError("Interview is not active.")

        question = self.current_question
        current_format = self.get_current_format()

        if not is_voice_mode and current_format == "MCQ":
            selected_letter = answer.strip()[0].upper()
            evaluation = evaluation_chain.invoke(
                {
                    "topic": self.topic,
                    "question": question.question,
                    "correct_answer": question.correct_answer,
                    "answer": selected_letter,
                }
            )
            stored_answer = answer
        else:
            written_eval = written_evaluation_chain.invoke(
                {"question": question.question, "answer": answer}
            )
            score = written_eval.score
            evaluation = Evaluation(
                score=score,
                is_correct=score >= 6,
                feedback=written_eval.feedback,
                follow_up_topic="",
            )
            stored_answer = answer

        self.questions.append(question)
        self.answers.append(stored_answer)
        self.evaluations.append(evaluation)
        self.formats_used.append(current_format)
        self.question_history.append(question.subtopic)
        self.question_index += 1
        self.subtopic_index += 1

        next_question = None
        if len(self.questions) >= self.num_questions:
            self.finished = True
            self.current_question = None
        else:
            next_question = self._generate_question(is_voice_mode=is_voice_mode)
            self.current_question = next_question

        return {
            "evaluation": evaluation,
            "finished": self.finished,
            "next_question": next_question,
            "current_format": self.get_current_format() if not self.finished else None,
        }

    def generate_report(self) -> dict:
        if not self.finished:
            raise ValueError("Interview is not finished.")

        interview_data = ""
        for i, (q, a, e) in enumerate(
            zip(self.questions, self.answers, self.evaluations)
        ):
            interview_data += f"""
Question {i + 1}

Topic:
{q.topic}

Subtopic:
{q.subtopic}

Question:
{q.question}

Candidate Answer:
{a}

Score:
{e.score}

Feedback:
{e.feedback}

=================================================

"""

        report: FinalReport = report_chain.invoke({"interview_data": interview_data})

        ideal_answers = []
        for q in self.questions:
            ideal = answer_chain.invoke(
                {
                    "topic": q.topic,
                    "difficulty": q.difficulty,
                    "question": q.question,
                }
            )
            ideal_answers.append(ideal)

        return {
            "report": report,
            "questions": self.questions,
            "answers": self.answers,
            "evaluations": self.evaluations,
            "formats_used": self.formats_used,
            "ideal_answers": ideal_answers,
            "name": self.name,
            "age": self.age,
            "experience": self.experience,
            "topic": self.topic,
            "difficulty": self.difficulty,
        }


_sessions: dict[str, InterviewSession] = {}


def create_session(
    name: str,
    age: int,
    experience: str,
    topic: str,
    difficulty: str,
    answer_format: str,
    num_questions: int,
    is_voice_mode: bool = False,
) -> InterviewSession:
    session_id = str(uuid.uuid4())
    session = InterviewSession(
        session_id=session_id,
        name=name,
        age=age,
        experience=experience,
        topic=topic,
        difficulty=difficulty,
        answer_format=answer_format,
        num_questions=num_questions,
    )
    session.start(is_voice_mode=is_voice_mode)
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> InterviewSession | None:
    return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
