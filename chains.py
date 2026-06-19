from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from schemas import (
    Question,
    Evaluation,
    WrittenEvaluation,
    FinalReport
)

# ============================================================
# LLM
# ============================================================

model = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3
)

# ============================================================
# QUESTION GENERATION
# ============================================================

question_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an expert technical interviewer.

Generate EXACTLY ONE interview MCQ.

TOPIC:
{topic}

SUBTOPIC:
{current_subtopic}

DIFFICULTY:
{difficulty}

CANDIDATE EXPERIENCE:
{experience}

PREVIOUSLY COVERED SUBTOPICS:
{history}

RULES:

1. Question MUST ONLY test:
   {current_subtopic}

2. Never repeat previous concepts.

3. Never repeat previous questions.

4. Difficulty must match:
   {difficulty}

5. Experience level must match:
   {experience}

6. Create EXACTLY four options:

A)
B)
C)
D)

7. Only ONE option should be correct.

8. Wrong options should be realistic.

9. Prefer interview-style conceptual questions.

10. Return fields:

question
topic
subtopic
difficulty
options
correct_answer
explanation

11. correct_answer must contain ONLY:
A or B or C or D

Question Style Requirements:

Randomly choose ONE of these styles:

12. Conceptual
13. Scenario-Based
14. Debugging
15. Code Analysis
16. Real World Application
17. Best Practice
18. System Design
19. Output Prediction
20. Interview Follow-up
21. Comparison Question

Do not repeatedly use:
- "What is the purpose of..."
- "What is the primary purpose of..."
- "Which of the following..."

Use a different style each time.

"""
    ),
    (
        "human",
        "Generate an interview question."
    )
])

question_chain = (
    question_prompt
    | model.with_structured_output(Question)
)

# ============================================================
# VOICE QUESTION GENERATION
# ============================================================

voice_question_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an expert technical interviewer conducting a live conversational interview.

Generate EXACTLY ONE open-ended interview question.

TOPIC:
{topic}

SUBTOPIC:
{current_subtopic}

DIFFICULTY:
{difficulty}

CANDIDATE EXPERIENCE:
{experience}

PREVIOUSLY COVERED SUBTOPICS:
{history}

RULES:

1. Question MUST ONLY test:
   {current_subtopic}

2. Never repeat previous concepts.

3. Never repeat previous questions.

4. Difficulty must match:
   {difficulty}

5. Experience level must match:
   {experience}

6. NEVER generate multiple-choice questions. Do not generate options. Do not provide correct answers or explanations.

7. Make it feel like a live human-to-human interview. Generates exactly ONE conversational question.

Return fields:

question
topic
subtopic
difficulty
"""
    ),
    (
        "human",
        "Generate a conversational interview question."
    )
])

voice_question_chain = (
    voice_question_prompt
    | model.with_structured_output(Question)
)

# ============================================================
# MCQ EVALUATION
# ============================================================

evaluation_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an interview evaluator.

QUESTION:
{question}

CORRECT ANSWER:
{correct_answer}

CANDIDATE ANSWER:
{answer}

TOPIC:
{topic}

RULES:

1. Compare ONLY answer letters.

2. If candidate answer equals correct answer:

score = 10
is_correct = true

3. Otherwise:

score = 0
is_correct = false

4. Explain why the correct answer is correct.

5. Provide concise constructive feedback.

6. Suggest a follow-up topic for improvement.
"""
    ),
    (
        "human",
        "Evaluate the candidate."
    )
])

evaluation_chain = (
    evaluation_prompt
    | model.with_structured_output(Evaluation)
)

# ============================================================
# WRITTEN ANSWER EVALUATION
# ============================================================

written_evaluation_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are a senior technical interviewer.

QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

Evaluate:

1. Technical Accuracy
2. Completeness
3. Clarity
4. Communication

Provide:

score (0-10)

feedback

strengths

weaknesses

Scoring Guide:

9-10 = Excellent
7-8 = Good
5-6 = Average
0-4 = Poor
"""
    ),
    (
        "human",
        "Evaluate this answer."
    )
])

written_evaluation_chain = (
    written_evaluation_prompt
    | model.with_structured_output(
        WrittenEvaluation
    )
)

# ============================================================
# FINAL REPORT
# ============================================================

report_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are a senior interview coach.

Analyze the interview.

INTERVIEW DATA:

{interview_data}

Generate:

overall_score

strengths

weaknesses

recommendations

summary

Be specific.

Do not give generic advice.

Focus on actual performance.
"""
    ),
    (
        "human",
        "Generate final report."
    )
])

report_chain = (
    report_prompt
    | model.with_structured_output(
        FinalReport
    )
)

# ============================================================
# IDEAL ANSWER GENERATION
# ============================================================

answer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an expert interviewer.

Provide an ideal answer.

TOPIC:
{topic}

DIFFICULTY:
{difficulty}

QUESTION:
{question}

RULES:

1. Maximum 5 lines.
2. Interview-ready.
3. Concise.
4. Technically accurate.
5. Clear explanation.
"""
    ),
    (
        "human",
        "Generate ideal answer."
    )
])

answer_chain = (
    answer_prompt
    | model
    | StrOutputParser()
)

# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":

    q = question_chain.invoke(
        {
            "topic": "Python",
            "current_subtopic": "Decorators",
            "difficulty": "medium",
            "experience": "Fresher",
            "history": []
        }
    )

    print("\nQUESTION\n")
    print(q)

    eval_result = evaluation_chain.invoke(
        {
            "question": q.question,
            "correct_answer": q.correct_answer,
            "answer": "A",
            "topic": "Python"
        }
    )

    print("\nEVALUATION\n")
    print(eval_result)

    written_result = written_evaluation_chain.invoke(
        {
            "question": "What is a decorator?",
            "answer": "A decorator modifies a function."
        }
    )

    print("\nWRITTEN EVALUATION\n")
    print(written_result)
