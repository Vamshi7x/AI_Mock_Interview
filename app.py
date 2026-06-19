
# ============================================================
# app.py
# SECTION 1/4
# ============================================================

import streamlit as st
import pandas as pd
import random
from datetime import datetime

from chains import (
    question_chain,
    evaluation_chain,
    written_evaluation_chain,
    report_chain,
    answer_chain
)

from schemas import (
    FinalReport
)

from subtopics import (
    SUBTOPICS
)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Mock Interviewer",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AI Mock Interviewer")

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🎯 AI Mock Interviewer")

    st.markdown(
        """
Practice:

- Python
- SQL
- Data Science
- GenAI
- DBMS
- Operating Systems
- Computer Networks
- Aptitude
- Logical Reasoning
- HR Interviews
"""
    )

    st.divider()

    st.info(
        """
Answer questions and receive:

✅ Evaluation

✅ Ideal Answers

✅ Performance Report

✅ Learning Recommendations
"""
    )

    st.divider()

    st.markdown(
        """
        <div style="text-align: center; color: #8b93a7; font-size: 0.85rem;">
            <p style="margin-bottom: 0.5rem; font-weight: 500;">Created by Vamshi</p>
            <a href="https://github.com/Vamshi7x" target="_blank" style="color: #8b93a7; margin-right: 15px; text-decoration: none;">GitHub</a>
            <a href="https://www.linkedin.com/in/vamshikummari7x/" target="_blank" style="color: #8b93a7; text-decoration: none;">LinkedIn</a>
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {

    "started": False,
    "finished": False,

    "name": "",
    "age": 22,

    "experience": "Fresher",

    "topic": "",
    "difficulty": "medium",

    "answer_format": "MCQ",

    "num_questions": 10,

    "current_question": None,

    "questions": [],
    "answers": [],
    "evaluations": [],

    "question_history": [],

    "question_index": 0,

    "subtopic_index": 0,

    "shuffled_subtopics": [],

    "formats_used": []
}

for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


QUESTION_STYLES = [
    "Conceptual",
    "Scenario",
    "Debugging",
    "Code Analysis",
    "Real World",
    "Comparison",
    "Output Prediction",
    "Best Practice"
]

style = random.choice(QUESTION_STYLES)

if "question_styles" not in st.session_state:
    st.session_state.question_styles = []

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def initialize_subtopics():

    topic_subtopics = SUBTOPICS.get(
        st.session_state.topic,
        ["General Concepts"]
    )

    st.session_state.shuffled_subtopics = (
        topic_subtopics.copy()
    )

    random.shuffle(
        st.session_state.shuffled_subtopics
    )


def get_next_subtopic():

    subtopics = (
        st.session_state.shuffled_subtopics
    )

    if len(subtopics) == 0:
        return "General Concepts"

    idx = (
        st.session_state.subtopic_index
        % len(subtopics)
    )

    return subtopics[idx]


def generate_question():

    current_subtopic = (
        get_next_subtopic()
    )

    question = question_chain.invoke(
        {
            "topic":
            st.session_state.topic,

            "current_subtopic":
            current_subtopic,

            "difficulty":
            st.session_state.difficulty,

            "experience":
            st.session_state.experience,

            "history":
            st.session_state.question_history
        }
    )

    return question


def reset_interview():

    for key in list(
        st.session_state.keys()
    ):
        del st.session_state[key]

    st.rerun()

# ============================================================
# INTERVIEW CONFIGURATION PAGE
# ============================================================

if not st.session_state.started:

    st.subheader(
        "Configure Interview"
    )

    col1, col2 = st.columns(2)

    with col1:

        name = st.text_input(
            "Candidate Name"
        )

        age = 22

        experience = st.radio(
            "Experience Level",
            [
                "Fresher",
                "Experienced"
            ]
        )

    with col2:

        topic = st.selectbox(
            "Topic",
            [
                "Python",
                "SQL",
                "Data Science / ML",
                "GenAI / LLM",
                "DBMS",
                "Operating Systems",
                "Computer Networks",
                "HR / Behavioral",
                "Aptitude",
                "Logical Reasoning"
            ]
        )

        difficulty = st.selectbox(
            "Difficulty",
            [
                "easy",
                "medium",
                "hard"
            ]
        )

        answer_format = st.radio(
            "Answer Format",
            [
                "MCQ",
                "Written",
                "Combined"
            ]
        )

    if answer_format == "MCQ":

        num_questions = st.slider(
            "Number of Questions",
            min_value=5,
            max_value=50,
            value=10,
            step=5
        )

    elif answer_format == "Written":

        num_questions = st.slider(
            "Number of Questions",
            min_value=3,
            max_value=20,
            value=5
        )

    else:

        num_questions = st.slider(
            "Number of Questions",
            min_value=5,
            max_value=30,
            value=10
        )

    st.divider()

    start_btn = st.button(
        "🚀 Start Interview",
        use_container_width=True
    )

    if start_btn:

        if not name.strip():

            st.warning(
                "Please enter your name."
            )

        else:

            st.session_state.started = True

            st.session_state.name = name
            st.session_state.age = age

            st.session_state.topic = topic

            st.session_state.difficulty = (
                difficulty
            )

            st.session_state.experience = (
                experience
            )

            st.session_state.answer_format = (
                answer_format
            )

            st.session_state.num_questions = (
                num_questions
            )

            st.session_state.question_index = 0

            st.session_state.subtopic_index = 0

            st.session_state.question_history = []

            st.session_state.questions = []

            st.session_state.answers = []

            st.session_state.evaluations = []

            st.session_state.formats_used = []

            initialize_subtopics()

            first_question = (
                generate_question()
            )

            st.session_state.current_question = (
                first_question
            )

            st.rerun()

# ============================================================
# INTERVIEW PAGE
# ============================================================

elif (
    st.session_state.started
    and
    not st.session_state.finished
):

    total_answered = len(
        st.session_state.questions
    )

    progress = (
        total_answered
        /
        st.session_state.num_questions
    )

    st.progress(progress)

    st.caption(
        f"Question {total_answered + 1}"
        f" of "
        f"{st.session_state.num_questions}"
    )

    question = (
        st.session_state.current_question
    )

    st.info(
        f"Topic: {question.topic}"
        f" | "
        f"Subtopic: {question.subtopic}"
    )

    st.subheader(
        question.question
    )



# ============================================================
# app.py
# SECTION 2/4
# ============================================================

    # --------------------------------------------------------
    # DETERMINE CURRENT FORMAT
    # --------------------------------------------------------

    if (
        st.session_state.answer_format
        == "Combined"
    ):

        current_format = (
            "MCQ"
            if total_answered % 2 == 0
            else "Written"
        )

    else:

        current_format = (
            st.session_state.answer_format
        )

    # ========================================================
    # MCQ MODE
    # ========================================================

    if current_format == "MCQ":

        selected_option = st.radio(
            "Choose your answer:",
            options=question.options,
            index=None,
            key=f"mcq_{total_answered}"
        )

        submit_mcq = st.button(
            "Submit Answer",
            use_container_width=True
        )

        if submit_mcq:

            if selected_option is None:

                st.warning(
                    "Please select an answer."
                )

            else:

                selected_letter = (
                    selected_option[0]
                )

                evaluation = (
                    evaluation_chain.invoke(
                        {
                            "topic":
                            st.session_state.topic,

                            "question":
                            question.question,

                            "correct_answer":
                            question.correct_answer,

                            "answer":
                            selected_letter
                        }
                    )
                )

                # --------------------------------------------
                # SAVE RESPONSE
                # --------------------------------------------

                st.session_state.questions.append(
                    question
                )

                st.session_state.answers.append(
                    selected_option
                )

                st.session_state.evaluations.append(
                    evaluation
                )

                st.session_state.formats_used.append(
                    "MCQ"
                )

                st.session_state.question_history.append(
                    question.subtopic
                )

                st.session_state.question_index += 1

                st.session_state.subtopic_index += 1

                # --------------------------------------------
                # INTERVIEW COMPLETE?
                # --------------------------------------------

                if (
                    len(
                        st.session_state.questions
                    )
                    >=
                    st.session_state.num_questions
                ):

                    st.session_state.finished = True

                else:

                    next_question = (
                        generate_question()
                    )

                    st.session_state.current_question = (
                        next_question
                    )

                st.rerun()

    # ========================================================
    # WRITTEN MODE
    # ========================================================

    elif current_format == "Written":

        answer = st.text_area(
            "Write your answer:",
            height=200
        )

        submit_written = st.button(
            "Submit Answer",
            use_container_width=True
        )

        if submit_written:

            if not answer.strip():

                st.warning(
                    "Please enter an answer."
                )

            else:

                written_eval = (
                    written_evaluation_chain.invoke(
                        {
                            "question":
                            question.question,

                            "answer":
                            answer
                        }
                    )
                )

                # --------------------------------------------
                # CONVERT TO COMMON FORMAT
                # --------------------------------------------

                score = (
                    written_eval.score
                )

                is_correct = (
                    score >= 6
                )

                feedback = (
                    written_eval.feedback
                )

                evaluation = type(
                    "WrittenResult",
                    (),
                    {
                        "score":
                        score,

                        "is_correct":
                        is_correct,

                        "feedback":
                        feedback,

                        "follow_up_topic":
                        ""
                    }
                )()

                # --------------------------------------------
                # SAVE RESPONSE
                # --------------------------------------------

                st.session_state.questions.append(
                    question
                )

                st.session_state.answers.append(
                    answer
                )

                st.session_state.evaluations.append(
                    evaluation
                )

                st.session_state.formats_used.append(
                    "Written"
                )

                st.session_state.question_history.append(
                    question.subtopic
                )

                st.session_state.question_index += 1

                st.session_state.subtopic_index += 1

                # --------------------------------------------
                # INTERVIEW COMPLETE?
                # --------------------------------------------

                if (
                    len(
                        st.session_state.questions
                    )
                    >=
                    st.session_state.num_questions
                ):

                    st.session_state.finished = True

                else:

                    next_question = (
                        generate_question()
                    )

                    st.session_state.current_question = (
                        next_question
                    )

                st.rerun()

    # ========================================================
    # CURRENT STATUS
    # ========================================================

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Answered",
            len(
                st.session_state.questions
            )
        )

    with col2:

        remaining = (
            st.session_state.num_questions
            -
            len(
                st.session_state.questions
            )
        )

        st.metric(
            "Remaining",
            remaining
        )

    with col3:

        st.metric(
            "Current Format",
            current_format
        )



# ============================================================
# app.py
# SECTION 3/4
# FINAL REPORT GENERATION
# ============================================================

elif st.session_state.finished:

    st.header("📊 Interview Report")

    # ========================================================
    # PREPARE INTERVIEW DATA
    # ========================================================

    interview_data = ""

    for i, (
        q,
        a,
        e
    ) in enumerate(
        zip(
            st.session_state.questions,
            st.session_state.answers,
            st.session_state.evaluations
        )
    ):

        interview_data += f"""

Question {i+1}

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

    # ========================================================
    # GENERATE REPORT
    # ========================================================

    report: FinalReport = (
        report_chain.invoke(
            {
                "interview_data":
                interview_data
            }
        )
    )

    # ========================================================
    # IDEAL ANSWERS
    # ========================================================

    ideal_answers = []

    with st.spinner(
        "Generating ideal answers..."
    ):

        for q in st.session_state.questions:

            ideal = (
                answer_chain.invoke(
                    {
                        "topic":
                        q.topic,

                        "difficulty":
                        q.difficulty,

                        "question":
                        q.question
                    }
                )
            )

            ideal_answers.append(
                ideal
            )

    # ========================================================
    # OVERALL METRICS
    # ========================================================

    st.subheader(
        "📈 Overall Performance"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Overall Score",
            f"{report.overall_score}/10"
        )

    with col2:

        total_questions = len(
            st.session_state.questions
        )

        st.metric(
            "Questions Attempted",
            total_questions
        )

    with col3:

        avg_score = round(
            sum(
                e.score
                for e in
                st.session_state.evaluations
            )
            /
            max(
                1,
                len(
                    st.session_state.evaluations
                )
            ),
            2
        )

        st.metric(
            "Average Score",
            avg_score
        )

    # ========================================================
    # SCORE TREND CHART
    # ========================================================

    st.subheader(
        "📊 Score Trend"
    )

    score_df = pd.DataFrame(
        {
            "Question":
            [
                f"Q{i+1}"
                for i in range(
                    len(
                        st.session_state.evaluations
                    )
                )
            ],

            "Score":
            [
                e.score
                for e in
                st.session_state.evaluations
            ]
        }
    )

    score_df = score_df.set_index(
        "Question"
    )

    st.line_chart(
        score_df
    )

    # ========================================================
    # TOPIC PERFORMANCE
    # ========================================================

    st.subheader(
        "📚 Topic Coverage"
    )

    topic_data = []

    for q, e in zip(
        st.session_state.questions,
        st.session_state.evaluations
    ):

        topic_data.append(
            {
                "Topic":
                q.topic,

                "Subtopic":
                q.subtopic,

                "Score":
                e.score
            }
        )

    topic_df = pd.DataFrame(
        topic_data
    )

    st.dataframe(
        topic_df,
        use_container_width=True
    )

    # ========================================================
    # QUESTION REVIEW
    # ========================================================

    st.subheader(
        "📝 Detailed Question Review"
    )

    for idx, (
        q,
        user_answer,
        evaluation,
        ideal_answer
    ) in enumerate(
        zip(
            st.session_state.questions,
            st.session_state.answers,
            st.session_state.evaluations,
            ideal_answers
        )
    ):

        with st.expander(
            f"Question {idx+1}: {q.subtopic}"
        ):

            st.markdown(
                f"### {q.question}"
            )

            st.markdown(
                f"**Topic:** {q.topic}"
            )

            st.markdown(
                f"**Subtopic:** {q.subtopic}"
            )

            # --------------------------------------------
            # OPTIONS
            # --------------------------------------------

            if (
                st.session_state.formats_used[idx]
                == "MCQ"
            ):

                st.markdown(
                    "### Options"
                )

                for opt in q.options:

                    if (
                        opt.startswith(
                            q.correct_answer
                        )
                    ):

                        st.success(opt)

                    else:

                        st.write(opt)

            # --------------------------------------------
            # USER ANSWER
            # --------------------------------------------

            st.markdown(
                "### Your Answer"
            )

            st.write(
                user_answer
            )

            # --------------------------------------------
            # EVALUATION
            # --------------------------------------------

            st.markdown(
                "### Evaluation"
            )

            st.write(
                f"Score: {evaluation.score}/10"
            )

            st.write(
                evaluation.feedback
            )

            # --------------------------------------------
            # EXPLANATION
            # --------------------------------------------

            st.markdown(
                "### Explanation"
            )

            st.write(
                q.explanation
            )

            # --------------------------------------------
            # IDEAL ANSWER
            # --------------------------------------------

            st.markdown(
                "### Ideal Answer"
            )

            st.info(
                ideal_answer
            )



# ============================================================
# app.py
# SECTION 4/4
# REPORT SUMMARY + DOWNLOAD + RESTART
# ============================================================

    # ========================================================
    # STRENGTHS
    # ========================================================

    st.subheader(
        "✅ Strengths"
    )

    if report.strengths:

        for strength in report.strengths:

            st.success(
                strength
            )

    else:

        st.info(
            "No strengths identified."
        )

    # ========================================================
    # WEAKNESSES
    # ========================================================

    st.subheader(
        "⚠️ Areas For Improvement"
    )

    if report.weaknesses:

        for weakness in report.weaknesses:

            st.warning(
                weakness
            )

    else:

        st.success(
            "No major weaknesses identified."
        )

    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    st.subheader(
        "📚 Recommended Topics"
    )

    if report.recommendations:

        for recommendation in (
            report.recommendations
        ):

            st.info(
                recommendation
            )

    else:

        st.info(
            "Keep practicing consistently."
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    st.subheader(
        "📝 Interview Summary"
    )

    st.markdown(
        report.summary
    )

    # ========================================================
    # BUILD DOWNLOAD REPORT
    # ========================================================

    report_text = f"""
=========================================================
AI MOCK INTERVIEW REPORT
=========================================================

Candidate Name:
{st.session_state.name}

Experience:
{st.session_state.experience}

Topic:
{st.session_state.topic}

Difficulty:
{st.session_state.difficulty}

Questions Attempted:
{len(st.session_state.questions)}

Overall Score:
{report.overall_score}/10


=========================================================
QUESTION REVIEW
=========================================================
"""

    for idx, (
        q,
        user_answer,
        evaluation
    ) in enumerate(
        zip(
            st.session_state.questions,
            st.session_state.answers,
            st.session_state.evaluations
        )
    ):

        report_text += f"""

---------------------------------------------------------
QUESTION {idx + 1}
---------------------------------------------------------

Topic:
{q.topic}

Subtopic:
{q.subtopic}

Question:
{q.question}

Candidate Answer:
{user_answer}

Correct Answer:
{q.correct_answer}

Explanation:
{q.explanation}

Score:
{evaluation.score}/10

Feedback:
{evaluation.feedback}

"""

    report_text += f"""

=========================================================
STRENGTHS
=========================================================

"""

    for item in report.strengths:

        report_text += f"""
- {item}
"""

    report_text += f"""

=========================================================
WEAKNESSES
=========================================================

"""

    for item in report.weaknesses:

        report_text += f"""
- {item}
"""

    report_text += f"""

=========================================================
RECOMMENDATIONS
=========================================================

"""

    for item in report.recommendations:

        report_text += f"""
- {item}
"""

    report_text += f"""

=========================================================
SUMMARY
=========================================================

{report.summary}

=========================================================
END OF REPORT
=========================================================
"""

    # ========================================================
    # DOWNLOAD BUTTON
    # ========================================================

    st.download_button(
        label="📥 Download Full Report",
        data=report_text,
        file_name=(
            f"{st.session_state.name}"
            "_interview_report.txt"
        ),
        mime="text/plain",
        use_container_width=True
    )

    # ========================================================
    # RESTART INTERVIEW
    # ========================================================

    st.divider()

    restart_col, spacer = st.columns(
        [1, 3]
    )

    with restart_col:

        restart = st.button(
            "🔄 Restart Interview",
            use_container_width=True
        )

        if restart:

            reset_interview()

# ============================================================
# END OF APP
# ============================================================
