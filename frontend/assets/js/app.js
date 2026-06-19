const API_BASE = "";

const TIMER_SECONDS = { MCQ: 60, Written: 120 };
const TIMER_RING_CIRCUMFERENCE = 97.4;

const state = {
  sessionId: null,
  currentQuestion: null,
  currentFormat: "MCQ",
  progress: { answered: 0, total: 10, remaining: 10 },
  reportData: null,
  selectedOption: null,
  writtenAnswer: "",
  scoreChart: null,
  history: [],
  viewingIndex: 0,
  timerInterval: null,
  timerRemaining: 0,
  isSubmitting: false,
  isVoiceMode: false,
  isAiSpeaking: false,
  isListening: false,
};

let recognition = null;
let synth = window.speechSynthesis;

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function initVoiceMode() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition || !synth) {
    return;
  }
  
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onresult = (event) => {
    let interimTranscript = '';
    let finalTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript;
      } else {
        interimTranscript += event.results[i][0].transcript;
      }
    }
    
    const liveEl = $("#voice-live-transcript");
    if (liveEl) {
      liveEl.textContent = state.writtenAnswer + finalTranscript + interimTranscript;
    }
    
    if (finalTranscript) {
      let isDone = false;
      if (finalTranscript.trim().toLowerCase().match(/\bdone\.?$/)) {
        isDone = true;
        finalTranscript = finalTranscript.replace(/\bdone\.?$/i, '').trim();
      }
      
      state.writtenAnswer += finalTranscript + (finalTranscript ? ' ' : '');
      $("#written-answer").value = state.writtenAnswer;
      
      if (isDone) {
        stopListening();
        submitAnswer({ timedOut: false });
      }
    }
  };

  recognition.onstart = () => {
    state.isListening = true;
    updateVoiceUI();
  };

  recognition.onend = () => {
    state.isListening = false;
    updateVoiceUI();
    if (state.isVoiceMode && !state.isAiSpeaking && !state.isSubmitting) {
      try { recognition.start(); } catch(e) {}
    }
  };
  
  recognition.onerror = (e) => {
    state.isListening = false;
    updateVoiceUI();
  };

  const floatBtn = $("#floating-voice-btn");
  if (floatBtn) {
    floatBtn.addEventListener("click", () => {
      state.isVoiceMode = true;
      updateVoiceUI();
      if (state.currentQuestion) {
        speak(state.currentQuestion.question, () => {
          startListening();
        }, true);
      }
    });
  }

  const exitBtn = $("#exit-voice-btn");
  if (exitBtn) {
    exitBtn.addEventListener("click", () => {
      state.isVoiceMode = false;
      stopListening();
      updateVoiceUI();
    });
  }

  const stopBtn = $("#stop-speaking-btn");
  if (stopBtn) {
    stopBtn.addEventListener("click", () => {
      stopListening();
      submitAnswer({ timedOut: false });
    });
  }
}

function updateVoiceUI() {
  const overlay = $("#voice-overlay");
  if (!overlay) return;

  if (!state.isVoiceMode || isViewingCurrent() === false) {
    overlay.classList.add("hidden");
    return;
  }
  
  overlay.classList.remove("hidden");
  
  const orb = $("#voice-orb");
  const stopBtn = $("#stop-speaking-btn");
  const transcriptEl = $("#voice-live-transcript");
  
  orb.className = "voice-orb";
  
  if (state.isAiSpeaking) {
    orb.classList.add("ai-speaking");
    stopBtn.classList.add("hidden");
    transcriptEl.textContent = state.writtenAnswer;
  } else if (state.isListening) {
    orb.classList.add("listening");
    stopBtn.classList.remove("hidden");
  } else {
    orb.classList.add("idle");
    stopBtn.classList.add("hidden");
  }

  if (!state.isAiSpeaking && state.currentQuestion) {
    $("#voice-question-text").textContent = state.currentQuestion.question;
  }
}

function speak(text, callback, isQuestion = false) {
  if (!state.isVoiceMode || !synth) {
    if (isQuestion) $("#question-text").textContent = text;
    if (callback) callback();
    return;
  }

  synth.cancel();
  
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95;
  utterance.pitch = 1.0;
  utterance.lang = 'en-US';

  if (isQuestion) {
    $("#voice-question-text").textContent = ""; 
    utterance.onboundary = (e) => {
      if (e.name === 'word') {
        $("#voice-question-text").textContent = text.slice(0, e.charIndex);
      }
    };
  }

  utterance.onstart = () => {
    state.isAiSpeaking = true;
    if (state.isListening && recognition) {
      try { recognition.stop(); } catch(e) {}
    }
    updateVoiceUI();
  };

  utterance.onend = () => {
    state.isAiSpeaking = false;
    if (isQuestion) {
      $("#voice-question-text").textContent = text;
    }
    updateVoiceUI();
    if (callback) callback();
  };
  
  utterance.onerror = () => {
    state.isAiSpeaking = false;
    if (isQuestion) {
      $("#voice-question-text").textContent = text;
    }
    updateVoiceUI();
    if (callback) callback();
  }

  synth.speak(utterance);
}

function startListening() {
  if (!state.isVoiceMode || !recognition) return;
  try {
    recognition.start();
  } catch (e) {}
}

function stopListening() {
  if (recognition) {
    try { recognition.stop(); } catch(e) {}
  }
  if (synth) {
    synth.cancel();
  }
  state.isAiSpeaking = false;
  state.isListening = false;
  updateVoiceUI();
}

function showView(viewId) {
  $$(".view").forEach((v) => v.classList.remove("active"));
  $(viewId).classList.add("active");
}

function showToast(message, isError = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 4000);
}

function setLoading(visible, message = "Loading...") {
  const overlay = $("#loading-overlay");
  $("#loading-message").textContent = message;
  overlay.classList.toggle("hidden", !visible);
}

function setButtonLoading(btn, loading) {
  btn.disabled = loading;
  btn.querySelector(".btn-text").classList.toggle("hidden", loading);
  btn.querySelector(".btn-spinner").classList.toggle("hidden", !loading);
}

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`);
  }

  return data;
}

function isViewingCurrent() {
  return state.viewingIndex === state.history.length;
}

function stopTimer() {
  if (state.timerInterval) {
    clearInterval(state.timerInterval);
    state.timerInterval = null;
  }
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function updateTimerDisplay() {
  const wrap = $("#timer-wrap");
  const text = $("#timer-text");
  const ring = $("#timer-ring");
  const total = TIMER_SECONDS[state.currentFormat] || 60;
  const pct = state.timerRemaining / total;

  text.textContent = formatTime(state.timerRemaining);
  ring.style.strokeDashoffset = TIMER_RING_CIRCUMFERENCE * (1 - pct);

  wrap.classList.remove("warning", "critical");
  if (state.timerRemaining <= 10) {
    wrap.classList.add("critical");
  } else if (state.timerRemaining <= 20) {
    wrap.classList.add("warning");
  }
}

function startTimer(format, resume = false) {
  stopTimer();

  if (!isViewingCurrent() || state.isSubmitting) {
    $("#timer-wrap").classList.add("hidden");
    return;
  }

  state.currentFormat = format;
  if (!resume) {
    state.timerRemaining = TIMER_SECONDS[format] || 60;
  }

  const wrap = $("#timer-wrap");
  wrap.classList.remove("hidden", "warning", "critical");
  updateTimerDisplay();

  state.timerInterval = setInterval(() => {
    state.timerRemaining -= 1;
    updateTimerDisplay();

    if (state.timerRemaining <= 0) {
      stopTimer();
      showToast("Time's up! Submitting your answer...");
      submitAnswer({ timedOut: true });
    }
  }, 1000);
}

function updateQuestionSlider(format) {
  const slider = $("#num_questions");
  const output = $("#num_questions-value");

  if (format === "MCQ") {
    slider.min = 5;
    slider.max = 50;
    slider.step = 5;
    slider.value = Math.min(Math.max(+slider.value, 5), 50);
  } else if (format === "Written") {
    slider.min = 3;
    slider.max = 20;
    slider.step = 1;
    slider.value = Math.min(Math.max(+slider.value, 3), 20);
  } else {
    slider.min = 5;
    slider.max = 30;
    slider.step = 1;
    slider.value = Math.min(Math.max(+slider.value, 5), 30);
  }

  output.textContent = slider.value;
}

function renderTopics(topics, selected = null) {
  const preview = $("#topic-preview");
  preview.innerHTML = topics
    .map((t) => `<li class="${t === selected ? "active" : ""}">${t}</li>`)
    .join("");

  const select = $("#topic");
  select.innerHTML = topics
    .map((t) => `<option value="${t}">${t}</option>`)
    .join("");
}

function renderQuestionNav() {
  const total = state.progress.total;
  const pillsEl = $("#question-pills");
  const currentIdx = state.history.length;

  pillsEl.innerHTML = Array.from({ length: total }, (_, i) => {
    let cls = "question-pill";
    if (i < state.history.length) cls += " answered";
    if (i === currentIdx && !state.progress.finished) cls += " current";
    if (i > currentIdx) cls += " future";
    if (i === state.viewingIndex) cls += " active";
    if (i < currentIdx && i === state.viewingIndex) cls += " reviewing";
    const disabled = i > currentIdx ? "disabled" : "";
    return `<button type="button" class="${cls}" data-index="${i}" ${disabled}>${i + 1}</button>`;
  }).join("");

  pillsEl.querySelectorAll(".question-pill:not(.future)").forEach((pill) => {
    pill.addEventListener("click", () => {
      navigateToQuestion(+pill.dataset.index);
    });
  });

  $("#prev-question").disabled = state.viewingIndex <= 0;
  $("#next-question").disabled = state.viewingIndex >= currentIdx;
}

function navigateToQuestion(index) {
  const maxIndex = state.history.length;
  if (index < 0 || index > maxIndex) return;

  stopTimer();
  stopListening();
  state.viewingIndex = index;

  if (isViewingCurrent()) {
    renderActiveQuestion(state.currentQuestion, state.currentFormat, true);
  } else {
    renderHistoricalQuestion(state.history[index]);
  }

  renderQuestionNav();
}

function goToCurrentQuestion() {
  navigateToQuestion(state.history.length);
}

function setReviewBanner(visible) {
  let banner = $("#review-banner");
  if (!banner) {
    const card = $(".question-card");
    banner = document.createElement("div");
    banner.id = "review-banner";
    banner.className = "review-banner hidden";
    banner.textContent =
      "Reviewing a previous question — answers cannot be changed.";
    card.insertBefore(banner, card.firstChild);
  }
  banner.classList.toggle("hidden", !visible);
}

function renderQuestionMeta(question) {
  $("#question-meta").innerHTML = `
    <span class="badge">${escapeHtml(question.topic)}</span>
    <span class="badge">${escapeHtml(question.subtopic)}</span>
    <span class="badge">${escapeHtml(question.difficulty)}</span>
  `;
}

function renderMcqOptions(question, { interactive, selectedAnswer }) {
  const mcqArea = $("#mcq-area");
  mcqArea.classList.remove("hidden");

  const optionsEl = $("#mcq-options");
  optionsEl.innerHTML = question.options
    .map(
      (opt, i) => `
      <label class="mcq-option${interactive ? "" : " disabled"}${selectedAnswer === opt ? " selected" : ""}" data-index="${i}">
        <input type="radio" name="mcq" value="${escapeAttr(opt)}" ${selectedAnswer === opt ? "checked" : ""} ${interactive ? "" : "disabled"} />
        <span>${escapeHtml(opt)}</span>
      </label>
    `
    )
    .join("");

  if (interactive) {
    optionsEl.querySelectorAll(".mcq-option").forEach((el) => {
      el.addEventListener("click", () => {
        optionsEl.querySelectorAll(".mcq-option").forEach((o) =>
          o.classList.remove("selected")
        );
        el.classList.add("selected");
        el.querySelector("input").checked = true;
        state.selectedOption = el.querySelector("input").value;
      });
    });
  }
}

function renderActiveQuestion(question, format, isResume = false) {
  state.currentQuestion = question;
  state.currentFormat = format;
  if (!isResume) {
    state.selectedOption = null;
    state.writtenAnswer = "";
  }

  setReviewBanner(false);
  renderQuestionMeta(question);

  const writtenArea = $("#written-area");
  const feedbackArea = $("#feedback-area");
  feedbackArea.classList.add("hidden");

  $("#submit-btn").classList.remove("hidden");
  $("#submit-btn").disabled = false;
  $("#back-to-current-btn").classList.add("hidden");

  const floatingBtn = $("#floating-voice-btn");
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (format === "Written" && SpeechRec && window.speechSynthesis) {
    floatingBtn.classList.remove("hidden");
  } else {
    floatingBtn.classList.add("hidden");
    if (state.isVoiceMode) {
      state.isVoiceMode = false;
      stopListening();
      updateVoiceUI();
    }
  }

  $("#question-text").textContent = question.question;

  if (format === "MCQ" && question.options && question.options.length > 0) {
    writtenArea.classList.add("hidden");
    renderMcqOptions(question, { interactive: true, selectedAnswer: state.selectedOption });
  } else {
    $("#mcq-area").classList.add("hidden");
    writtenArea.classList.remove("hidden");
    const textarea = $("#written-answer");
    textarea.value = state.writtenAnswer;
    textarea.disabled = false;
  }

  updateProgressUI(state.progress, format);
  renderQuestionNav();
  startTimer(format, isResume);

  updateVoiceUI();
  const transcriptEl = $("#voice-live-transcript");
  if (transcriptEl) transcriptEl.textContent = state.writtenAnswer;
  
  if (state.isVoiceMode && !isResume) {
    speak(question.question, () => {
      startListening();
    }, true);
  }
}

function renderHistoricalQuestion(item) {
  setReviewBanner(true);
  stopTimer();
  $("#timer-wrap").classList.add("hidden");

  const { question, answer, evaluation, format } = item;
  renderQuestionMeta(question);
  $("#question-text").textContent = question.question;

  const mcqArea = $("#mcq-area");
  const writtenArea = $("#written-area");
  const feedbackArea = $("#feedback-area");

  if (format === "MCQ" && question.options && question.options.length > 0) {
    writtenArea.classList.add("hidden");
    renderMcqOptions(question, { interactive: false, selectedAnswer: answer });
  } else {
    mcqArea.classList.add("hidden");
    writtenArea.classList.remove("hidden");
    const textarea = $("#written-answer");
    textarea.value = answer;
    textarea.disabled = true;
  }

  showFeedback(evaluation);
  feedbackArea.classList.remove("hidden");

  $("#submit-btn").classList.add("hidden");
  const backBtn = $("#back-to-current-btn");
  backBtn.classList.remove("hidden");
  backBtn.disabled = false;

  updateProgressUI(state.progress, format);
  renderQuestionNav();
}

function renderQuestion(question, format) {
  state.viewingIndex = state.history.length;
  renderActiveQuestion(question, format);
}

function updateProgressUI(progress, format) {
  const pct = progress.total ? (progress.answered / progress.total) * 100 : 0;

  $("#progress-bar").style.width = `${pct}%`;

  if (isViewingCurrent()) {
    $("#progress-label").textContent = progress.finished
      ? "Interview complete"
      : `Question ${progress.answered + 1} of ${progress.total}`;
  } else {
    $("#progress-label").textContent = `Reviewing question ${state.viewingIndex + 1} of ${progress.total}`;
  }

  $("#stat-answered").textContent = progress.answered;
  $("#stat-remaining").textContent = progress.remaining;
  $("#stat-format").textContent = format || "—";
}

function showFeedback(evaluation) {
  const area = $("#feedback-area");
  area.classList.remove("hidden", "success", "partial", "fail");

  const score = evaluation.score;
  if (score >= 8) area.classList.add("success");
  else if (score >= 5) area.classList.add("partial");
  else area.classList.add("fail");

  $("#feedback-score").textContent = `Score: ${score}/10`;
  $("#feedback-text").textContent = evaluation.feedback;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function escapeAttr(str) {
  return escapeHtml(str).replace(/"/g, "&quot;");
}

async function submitAnswer({ timedOut = false } = {}) {
  if (!isViewingCurrent() || state.isSubmitting) return;

  let answer = "";

  if (state.currentFormat === "MCQ") {
    if (state.selectedOption) {
      answer = state.selectedOption;
    } else if (state.isVoiceMode && state.writtenAnswer) {
      answer = state.writtenAnswer;
    } else if (timedOut) {
      answer = "X";
    } else {
      showToast("Please select an answer.", true);
      return;
    }
  } else {
    answer = $("#written-answer").value.trim();
    if (!answer) {
      answer = timedOut
        ? "(Time expired — no answer submitted)"
        : "";
    }
    if (!answer && !timedOut) {
      showToast("Please enter an answer.", true);
      return;
    }
  }

  stopTimer();
  stopListening();
  state.isSubmitting = true;

  const btn = $("#submit-btn");
  setButtonLoading(btn, true);

  const submittedQuestion = state.currentQuestion;
  const submittedFormat = state.currentFormat;

  try {
    setLoading(true, timedOut ? "Time expired — evaluating..." : "Evaluating answer...");
    const data = await api(`/api/sessions/${state.sessionId}/submit`, {
      method: "POST",
      body: JSON.stringify({ answer, is_voice_mode: state.isVoiceMode }),
    });

    state.progress = data.progress;

    state.history.push({
      question: submittedQuestion,
      answer,
      evaluation: data.evaluation,
      format: submittedFormat,
    });

    state.viewingIndex = state.history.length;
    showFeedback(data.evaluation);
    btn.disabled = true;

    if (data.finished) {
      if (state.isVoiceMode) {
        speak("Got it. " + data.evaluation.feedback, () => {
          setLoading(true, "Generating full report...");
          api(`/api/sessions/${state.sessionId}/report`).then(report => {
            state.isVoiceMode = false;
            updateVoiceUI();
            renderReport(report);
            showView("#view-report");
            setLoading(false);
          });
        });
      } else {
        setLoading(true, "Generating full report...");
        const report = await api(`/api/sessions/${state.sessionId}/report`);
        renderReport(report);
        showView("#view-report");
      }
    } else {
      if (state.isVoiceMode) {
        speak("Got it. Moving to next question.", () => {
          state.isSubmitting = false;
          renderQuestion(data.next_question, data.current_format);
        });
      } else {
        if (!timedOut) {
          await new Promise((r) => setTimeout(r, 1200));
        }
        state.isSubmitting = false;
        renderQuestion(data.next_question, data.current_format);
      }
    }
  } catch (err) {
    showToast(err.message, true);
    state.isSubmitting = false;
    startTimer(state.currentFormat, state.timerRemaining > 0);
  } finally {
    state.isSubmitting = false;
    setButtonLoading(btn, false);
    setLoading(false);
  }
}

function renderReport(data) {
  stopTimer();
  state.reportData = data;
  const { report, questions, answers, evaluations, ideal_answers, formats_used } =
    data;

  $("#report-subtitle").textContent = `${data.name} · ${data.topic} · ${data.difficulty}`;

  $("#overall-score").textContent = `${report.overall_score}/10`;
  $("#questions-attempted").textContent = questions.length;

  const avg =
    evaluations.reduce((s, e) => s + e.score, 0) /
    Math.max(1, evaluations.length);
  $("#average-score").textContent = avg.toFixed(1);

  renderScoreChart(evaluations);

  fillList("#strengths-list", report.strengths, "No strengths identified.");
  fillList("#weaknesses-list", report.weaknesses, "No major weaknesses.");
  fillList(
    "#recommendations-list",
    report.recommendations,
    "Keep practicing consistently."
  );

  $("#summary-text").textContent = report.summary;

  const reviewEl = $("#question-review");
  reviewEl.innerHTML = questions
    .map((q, i) => {
      const eval_ = evaluations[i];
      const isMcq = formats_used[i] === "MCQ";

      let optionsHtml = "";
      if (isMcq && q.options) {
        optionsHtml = `
          <h5>Options</h5>
          ${q.options
            .map((opt) =>
              opt.startsWith(q.correct_answer)
                ? `<p class="option-correct">${escapeHtml(opt)}</p>`
                : `<p>${escapeHtml(opt)}</p>`
            )
            .join("")}
        `;
      }

      return `
        <div class="review-item">
          <div class="review-header" data-index="${i}">
            <h4>Question ${i + 1}: ${escapeHtml(q.subtopic)}</h4>
            <span class="review-score">${eval_.score}/10</span>
          </div>
          <div class="review-body">
            <h5>Question</h5>
            <p>${escapeHtml(q.question)}</p>
            ${optionsHtml}
            <h5>Your Answer</h5>
            <p>${escapeHtml(answers[i])}</p>
            <h5>Evaluation</h5>
            <p>${escapeHtml(eval_.feedback)}</p>
            <h5>Explanation</h5>
            <p>${escapeHtml(q.explanation)}</p>
            <h5>Ideal Answer</h5>
            <p class="ideal-answer">${escapeHtml(ideal_answers[i])}</p>
          </div>
        </div>
      `;
    })
    .join("");

  reviewEl.querySelectorAll(".review-header").forEach((header) => {
    header.addEventListener("click", () => {
      header.parentElement.classList.toggle("open");
    });
  });
}

function fillList(selector, items, emptyMsg) {
  const el = $(selector);
  if (!items || items.length === 0) {
    el.innerHTML = `<li>${emptyMsg}</li>`;
    return;
  }
  el.innerHTML = items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderScoreChart(evaluations) {
  const canvas = $("#score-chart");
  if (state.scoreChart) {
    state.scoreChart.destroy();
  }

  state.scoreChart = new Chart(canvas, {
    type: "line",
    data: {
      labels: evaluations.map((_, i) => `Q${i + 1}`),
      datasets: [
        {
          label: "Score",
          data: evaluations.map((e) => e.score),
          borderColor: "#818cf8",
          backgroundColor: "rgba(99, 102, 241, 0.15)",
          fill: true,
          tension: 0.3,
          pointRadius: 5,
          pointBackgroundColor: "#6366f1",
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: {
          min: 0,
          max: 10,
          grid: { color: "#2a3142" },
          ticks: { color: "#8b93a7" },
        },
        x: {
          grid: { color: "#2a3142" },
          ticks: { color: "#8b93a7" },
        },
      },
      plugins: {
        legend: { display: false },
      },
    },
  });
}

function buildReportText(data) {
  const { report, questions, answers, evaluations, name, experience, topic, difficulty } =
    data;

  let text = `
=========================================================
AI MOCK INTERVIEW REPORT
=========================================================

Candidate Name: ${name}
Experience: ${experience}
Topic: ${topic}
Difficulty: ${difficulty}
Questions Attempted: ${questions.length}
Overall Score: ${report.overall_score}/10

=========================================================
QUESTION REVIEW
=========================================================
`;

  questions.forEach((q, i) => {
    text += `
---------------------------------------------------------
QUESTION ${i + 1}
---------------------------------------------------------

Topic: ${q.topic}
Subtopic: ${q.subtopic}
Question: ${q.question}
Candidate Answer: ${answers[i]}
Correct Answer: ${q.correct_answer}
Explanation: ${q.explanation}
Score: ${evaluations[i].score}/10
Feedback: ${evaluations[i].feedback}
`;
  });

  text += `
=========================================================
STRENGTHS
=========================================================
${report.strengths.map((s) => `- ${s}`).join("\n")}

=========================================================
WEAKNESSES
=========================================================
${report.weaknesses.map((w) => `- ${w}`).join("\n")}

=========================================================
RECOMMENDATIONS
=========================================================
${report.recommendations.map((r) => `- ${r}`).join("\n")}

=========================================================
SUMMARY
=========================================================

${report.summary}

=========================================================
END OF REPORT
=========================================================
`;

  return text;
}

function resetInterviewState() {
  stopTimer();
  stopListening();
  state.isVoiceMode = false;
  updateVoiceUI();
  state.sessionId = null;
  state.reportData = null;
  state.history = [];
  state.viewingIndex = 0;
  state.currentQuestion = null;
  state.isSubmitting = false;
  state.selectedOption = null;
  state.writtenAnswer = "";
  if (state.scoreChart) {
    state.scoreChart.destroy();
    state.scoreChart = null;
  }
}

async function init() {
  initVoiceMode();
  try {
    const { topics } = await api("/api/topics");
    renderTopics(topics);
  } catch {
    showToast("Could not load topics. Is the API running?", true);
  }

  $("#topic").addEventListener("change", (e) => {
    const topic = e.target.value;
    $$("#topic-preview li").forEach((li) => {
      li.classList.toggle("active", li.textContent === topic);
    });
  });

  $$('input[name="answer_format"]').forEach((radio) => {
    radio.addEventListener("change", (e) => {
      updateQuestionSlider(e.target.value);
    });
  });

  $("#num_questions").addEventListener("input", (e) => {
    $("#num_questions-value").textContent = e.target.value;
  });

  $("#prev-question").addEventListener("click", () => {
    navigateToQuestion(state.viewingIndex - 1);
  });

  $("#next-question").addEventListener("click", () => {
    navigateToQuestion(state.viewingIndex + 1);
  });

  $("#back-to-current-btn").addEventListener("click", () => {
    goToCurrentQuestion();
  });

  $("#written-answer").addEventListener("input", (e) => {
    state.writtenAnswer = e.target.value;
  });

  $("#config-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = $("#start-btn");
    setButtonLoading(btn, true);

    const form = e.target;
    const body = {
      name: form.name.value.trim(),
      age: 22,
      experience: form.experience.value,
      topic: form.topic.value,
      difficulty: form.difficulty.value,
      answer_format: form.answer_format.value,
      num_questions: +form.num_questions.value,
      is_voice_mode: state.isVoiceMode,
    };

    try {
      resetInterviewState();
      setLoading(true, "Generating first question...");
      const data = await api("/api/sessions", {
        method: "POST",
        body: JSON.stringify(body),
      });

      state.sessionId = data.session_id;
      state.progress = data.progress;
      renderQuestion(data.question, data.current_format);
      showView("#view-interview");
    } catch (err) {
      showToast(err.message, true);
    } finally {
      setButtonLoading(btn, false);
      setLoading(false);
    }
  });

  $("#submit-btn").addEventListener("click", () => {
    submitAnswer({ timedOut: false });
  });

  $("#download-btn").addEventListener("click", () => {
    if (!state.reportData) return;
    const text = buildReportText(state.reportData);
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${state.reportData.name}_interview_report.txt`;
    a.click();
    URL.revokeObjectURL(url);
  });

  $("#restart-btn").addEventListener("click", async () => {
    if (state.sessionId) {
      try {
        await api(`/api/sessions/${state.sessionId}`, { method: "DELETE" });
      } catch {
        /* ignore */
      }
    }

    resetInterviewState();
    $("#config-form").reset();
    updateQuestionSlider("MCQ");
    showView("#view-config");
  });
}

init();
