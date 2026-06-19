"""FastAPI backend for AI Mock Interviewer."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from session_store import create_session, delete_session, get_session
from subtopics import SUBTOPICS

FRONTEND_DIR = Path(__file__).parent / "frontend"

app = FastAPI(
    title="AI Mock Interviewer API",
    description="REST API for the AI Mock Interviewer application",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


TOPICS = [
    "Python",
    "SQL",
    "Data Science / ML",
    "GenAI / LLM",
    "DBMS",
    "Operating Systems",
    "Computer Networks",
    "HR / Behavioral",
    "Aptitude",
    "Logical Reasoning",
]


class CreateSessionRequest(BaseModel):
    name: str = Field(min_length=1)
    age: int = Field(default=22, ge=18, le=60)
    experience: str = Field(default="Fresher")
    topic: str
    difficulty: str = Field(default="medium")
    answer_format: str = Field(default="MCQ")
    num_questions: int = Field(default=10, ge=3, le=50)
    is_voice_mode: bool = Field(default=False)


class SubmitAnswerRequest(BaseModel):
    answer: str = Field(min_length=1)
    is_voice_mode: bool = Field(default=False)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/topics")
def list_topics():
    return {"topics": TOPICS}


@app.get("/api/subtopics/{topic}")
def list_subtopics(topic: str):
    subtopics = SUBTOPICS.get(topic, ["General Concepts"])
    return {"topic": topic, "subtopics": subtopics}


@app.post("/api/sessions")
def start_session(body: CreateSessionRequest):
    if body.topic not in TOPICS:
        raise HTTPException(status_code=400, detail="Invalid topic.")

    if body.experience not in ("Fresher", "Experienced"):
        raise HTTPException(status_code=400, detail="Invalid experience level.")

    if body.difficulty not in ("easy", "medium", "hard"):
        raise HTTPException(status_code=400, detail="Invalid difficulty.")

    if body.answer_format not in ("MCQ", "Written", "Combined"):
        raise HTTPException(status_code=400, detail="Invalid answer format.")

    session = create_session(
        name=body.name.strip(),
        age=body.age,
        experience=body.experience,
        topic=body.topic,
        difficulty=body.difficulty,
        answer_format=body.answer_format,
        num_questions=body.num_questions,
        is_voice_mode=body.is_voice_mode,
    )

    question = session.current_question
    return {
        "session_id": session.session_id,
        "question": question.model_dump() if question else None,
        "current_format": session.get_current_format(),
        "progress": {
            "answered": 0,
            "total": session.num_questions,
            "remaining": session.num_questions,
        },
    }


@app.get("/api/sessions/{session_id}")
def get_session_state(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    return {
        "session_id": session.session_id,
        "name": session.name,
        "topic": session.topic,
        "difficulty": session.difficulty,
        "answer_format": session.answer_format,
        "finished": session.finished,
        "current_format": session.get_current_format() if not session.finished else None,
        "question": (
            session.current_question.model_dump()
            if session.current_question
            else None
        ),
        "progress": {
            "answered": len(session.questions),
            "total": session.num_questions,
            "remaining": session.num_questions - len(session.questions),
        },
    }


@app.post("/api/sessions/{session_id}/submit")
def submit_answer(session_id: str, body: SubmitAnswerRequest):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session.finished:
        raise HTTPException(status_code=400, detail="Interview already finished.")

    try:
        result = session.submit_answer(body.answer.strip(), is_voice_mode=body.is_voice_mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    evaluation = result["evaluation"]
    next_question = result["next_question"]

    return {
        "evaluation": {
            "score": evaluation.score,
            "is_correct": evaluation.is_correct,
            "feedback": evaluation.feedback,
            "follow_up_topic": getattr(evaluation, "follow_up_topic", ""),
        },
        "finished": result["finished"],
        "next_question": (
            next_question.model_dump() if next_question else None
        ),
        "current_format": result["current_format"],
        "progress": {
            "answered": len(session.questions),
            "total": session.num_questions,
            "remaining": session.num_questions - len(session.questions),
        },
    }


@app.get("/api/sessions/{session_id}/report")
def get_report(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if not session.finished:
        raise HTTPException(
            status_code=400,
            detail="Interview must be completed before generating a report.",
        )

    try:
        data = session.generate_report()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    report = data["report"]
    return {
        "name": data["name"],
        "age": data["age"],
        "experience": data["experience"],
        "topic": data["topic"],
        "difficulty": data["difficulty"],
        "report": report.model_dump(),
        "questions": [q.model_dump() for q in data["questions"]],
        "answers": data["answers"],
        "evaluations": [
            {
                "score": e.score,
                "is_correct": e.is_correct,
                "feedback": e.feedback,
            }
            for e in data["evaluations"]
        ],
        "formats_used": data["formats_used"],
        "ideal_answers": data["ideal_answers"],
    }


@app.delete("/api/sessions/{session_id}")
def end_session(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    delete_session(session_id)
    return {"deleted": True}


if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/")
    def serve_frontend():
        return FileResponse(FRONTEND_DIR / "index.html")
