let workoutState = null;
let historyItems = [];
let editingSessionId = null;
const historyDetailCache = new Map();
const PLATE_SCALE = 4;
const WORKOUT_EXERCISES = {
  A: ["Squat", "Bench Press", "Barbell Row"],
  B: ["Squat", "Overhead Press", "Deadlift"],
};

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function cycleRep(button) {
  let value = Number(button.dataset.reps || "5");
  value = value <= 0 ? 5 : value - 1;
  button.dataset.reps = String(value);
  button.textContent = String(value);
  button.classList.toggle("zero", value === 0);
}

function renderWorkout(state) {
  workoutState = state;
  if (editingSessionId) {
    document.getElementById("workoutTitle").textContent = `Workout ${state.workout} (Editing #${editingSessionId})`;
  } else {
    document.getElementById("workoutTitle").textContent = `Workout ${state.workout}`;
  }

  const list = document.getElementById("workoutList");
  const tpl = document.getElementById("exerciseTemplate");
  list.innerHTML = "";

  state.exercises.forEach((exercise) => {
    const node = tpl.content.cloneNode(true);
    node.querySelector(".exercise-name").textContent = exercise.name;

    const weightInput = node.querySelector(".weight-input");
    weightInput.value = exercise.weight;
    const notesBtn = node.querySelector(".notes-btn");
    const notesInput = node.querySelector(".notes-input");
    const notesText = (exercise.notes || "").trim();
    notesInput.value = notesText;
    const hasNotes = notesText.length > 0;
    notesInput.classList.toggle("hidden", !hasNotes);
    notesBtn.textContent = hasNotes ? "Hide Notes" : "Add Notes";
    notesBtn.addEventListener("click", () => {
      const enabled = notesInput.classList.contains("hidden");
      notesInput.classList.toggle("hidden", !enabled);
      notesBtn.textContent = enabled ? "Hide Notes" : "Add Notes";
      if (!enabled) {
        notesInput.value = "";
      } else {
        notesInput.focus();
      }
    });

    const btnWrap = node.querySelector(".set-buttons");
    exercise.sets.forEach((reps, idx) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "set-btn";
      btn.dataset.reps = String(reps);
      btn.dataset.index = String(idx);
      btn.textContent = String(reps);
      btn.addEventListener("click", () => cycleRep(btn));
      btnWrap.appendChild(btn);
    });

    list.appendChild(node);
  });
}

function collectWorkout() {
  const cards = document.querySelectorAll(".exercise-card");
  const exercises = [];

  cards.forEach((card) => {
    const name = card.querySelector(".exercise-name").textContent;
    const weight = Number(card.querySelector(".weight-input").value || "0");
    const sets = [...card.querySelectorAll(".set-btn")].map((b) => Number(b.dataset.reps || "0"));
    const notesInput = card.querySelector(".notes-input");
    const notesEnabled = !notesInput.classList.contains("hidden");
    const notes = notesEnabled ? notesInput.value.trim() : "";
    exercises.push({ name, weight, sets, notes });
  });

  return {
    workout: workoutState.workout,
    exercises,
  };
}

async function loadState() {
  const res = await fetch("/api/state");
  const state = await res.json();
  renderWorkout(state);
}

function renderSessionDetails(container, detail) {
  const grouped = new Map();
  const notesByExercise = detail.notes || {};
  detail.sets.forEach((setRow) => {
    if (!grouped.has(setRow.exercise_name)) {
      grouped.set(setRow.exercise_name, []);
    }
    grouped.get(setRow.exercise_name).push(setRow);
  });

  const lines = [];
  grouped.forEach((rows, exercise) => {
    const setText = rows.map((row) => `${row.completed_reps}`).join("/");
    const weight = rows[0].weight;
    const noteText = (notesByExercise[exercise] || "").trim();
    const noteHtml = noteText ? `<div>Notes: ${escapeHtml(noteText)}</div>` : "";
    lines.push(
      `<div><strong>${escapeHtml(exercise)}</strong>: ${setText} @ ${weight} lb${noteHtml}</div>`
    );
  });

  container.innerHTML = lines.join("");
}

async function toggleSessionDetails(linkEl, sessionId, detailEl) {
  const expanded = linkEl.dataset.expanded === "1";

  if (expanded) {
    detailEl.classList.add("hidden");
    linkEl.dataset.expanded = "0";
    linkEl.textContent = "View";
    return;
  }

  if (!detailEl.dataset.loaded) {
    let detail;
    try {
      detail = await getSessionDetail(sessionId);
    } catch (_err) {
      detailEl.textContent = "Failed to load workout details.";
      detailEl.classList.remove("hidden");
      return;
    }
    renderSessionDetails(detailEl, detail);
    detailEl.dataset.loaded = "1";
  }

  detailEl.classList.remove("hidden");
  linkEl.dataset.expanded = "1";
  linkEl.textContent = "Hide";
}

function toLocalYmd(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function atLocalMidnight(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function addDays(date, days) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days);
}

function dayDiff(a, b) {
  const msPerDay = 24 * 60 * 60 * 1000;
  return Math.round((atLocalMidnight(a) - atLocalMidnight(b)) / msPerDay);
}

function parseYmd(ymd) {
  const [y, m, d] = ymd.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function getScheduleAnchor(history) {
  if (history.length > 0) {
    const latest = [...history].sort(
      (a, b) => new Date(b.completed_at) - new Date(a.completed_at)
    )[0];
    return {
      date: atLocalMidnight(new Date(latest.completed_at)),
      workout: latest.workout,
    };
  }

  if (workoutState?.workout) {
    return {
      date: atLocalMidnight(new Date()),
      workout: workoutState.workout,
    };
  }

  return null;
}

function getExpectedWorkoutForDate(targetDate, history) {
  const anchor = getScheduleAnchor(history);
  if (!anchor) {
    return { scheduled: false, workout: null };
  }

  const delta = dayDiff(targetDate, anchor.date);
  if (Math.abs(delta) % 2 !== 0) {
    return { scheduled: false, workout: null };
  }

  let workout = anchor.workout;
  const swaps = Math.abs(delta) / 2;
  if (swaps % 2 === 1) {
    workout = workout === "A" ? "B" : "A";
  }

  return { scheduled: true, workout };
}

async function getSessionDetail(sessionId) {
  if (historyDetailCache.has(sessionId)) {
    return historyDetailCache.get(sessionId);
  }

  const res = await fetch(`/api/history/${sessionId}`);
  if (!res.ok) {
    throw new Error("Failed to load workout details");
  }

  const detail = await res.json();
  historyDetailCache.set(sessionId, detail);
  return detail;
}

function formatSessionSummary(detail) {
  const grouped = new Map();
  const notesByExercise = detail.notes || {};
  detail.sets.forEach((setRow) => {
    if (!grouped.has(setRow.exercise_name)) {
      grouped.set(setRow.exercise_name, []);
    }
    grouped.get(setRow.exercise_name).push(setRow);
  });

  const lines = [];
  grouped.forEach((rows, exercise) => {
    const setText = rows.map((row) => `${row.completed_reps}`).join("/");
    const weight = rows[0].weight;
    const noteText = (notesByExercise[exercise] || "").trim();
    const noteHtml = noteText ? `<div>Notes: ${escapeHtml(noteText)}</div>` : "";
    lines.push(
      `<div><strong>${escapeHtml(exercise)}</strong>: ${setText} @ ${weight} lb${noteHtml}</div>`
    );
  });

  return lines.join("");
}

async function showCalendarDayDetails(ymd, cellEl) {
  document.querySelectorAll(".calendar-day.selected").forEach((el) => el.classList.remove("selected"));
  if (cellEl) {
    cellEl.classList.add("selected");
  }

  const detailEl = document.getElementById("calendarDetail");
  const sessions = historyItems
    .filter((item) => toLocalYmd(new Date(item.completed_at)) === ymd)
    .sort((a, b) => new Date(a.completed_at) - new Date(b.completed_at));

  if (sessions.length === 0) {
    const selectedDate = parseYmd(ymd);
    const today = atLocalMidnight(new Date());
    const expected = getExpectedWorkoutForDate(selectedDate, historyItems);

    if (expected.scheduled) {
      if (selectedDate < today) {
        detailEl.innerHTML = `<div><strong>${ymd}</strong>: No workout logged. Workout ${expected.workout} should have happened.</div>`;
      } else {
        detailEl.innerHTML = `<div><strong>${ymd}</strong>: No workout logged yet. Planned workout: ${expected.workout}.</div>`;
      }
    } else {
      detailEl.innerHTML = `<div><strong>${ymd}</strong>: No workout scheduled.</div>`;
    }
    return;
  }

  detailEl.textContent = "Loading workout details...";
  try {
    const details = await Promise.all(sessions.map((s) => getSessionDetail(s.id)));
    const html = details
      .map((detail) => {
        const when = new Date(detail.completed_at).toLocaleTimeString([], {
          hour: "numeric",
          minute: "2-digit",
        });
        return `
          <div class="calendar-detail-session">
            <div><strong>${ymd}</strong> - Workout ${detail.workout} (${when})</div>
            ${formatSessionSummary(detail)}
          </div>
        `;
      })
      .join("");
    detailEl.innerHTML = html;
  } catch (_err) {
    detailEl.textContent = "Could not load workout details for this day.";
  }
}

function renderCalendar(history) {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const first = new Date(year, month, 1);
  const startWeekday = first.getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  document.getElementById("calendarMonth").textContent = now.toLocaleDateString(undefined, {
    month: "long",
    year: "numeric",
  });

  const completedSet = new Set();
  history.forEach((item) => {
    completedSet.add(toLocalYmd(new Date(item.completed_at)));
  });

  const today = atLocalMidnight(new Date());
  const grid = document.getElementById("calendarGrid");
  grid.innerHTML = "";

  for (let i = 0; i < startWeekday; i += 1) {
    const empty = document.createElement("div");
    empty.className = "calendar-day empty";
    grid.appendChild(empty);
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    const date = new Date(year, month, day);
    const ymd = toLocalYmd(date);

    const cell = document.createElement("div");
    cell.className = "calendar-day";

    const expected = getExpectedWorkoutForDate(date, history);

    if (completedSet.has(ymd)) {
      cell.classList.add("workout-done");
    } else if (expected.scheduled && atLocalMidnight(date) >= today) {
      cell.classList.add("future-workout");
    }

    const num = document.createElement("span");
    num.className = "day-num";
    num.textContent = String(day);

    cell.addEventListener("click", () => {
      showCalendarDayDetails(ymd, cell);
    });

    cell.appendChild(num);
    grid.appendChild(cell);
  }
}

async function loadHistory() {
  const res = await fetch("/api/history");
  const items = await res.json();
  historyItems = items;

  const list = document.getElementById("historyList");
  list.innerHTML = "";

  items.forEach((item) => {
    const wrapper = document.createElement("div");
    wrapper.className = "history-item";

    const row = document.createElement("div");
    row.className = "history-row";

    const text = document.createElement("span");
    const when = new Date(item.completed_at).toLocaleString();
    text.textContent = `${when} - Workout ${item.workout}`;

    const actions = document.createElement("div");
    actions.className = "history-actions";

    const viewBtn = document.createElement("button");
    viewBtn.type = "button";
    viewBtn.className = "history-link";
    viewBtn.textContent = "View";
    viewBtn.dataset.expanded = "0";

    const editBtn = document.createElement("button");
    editBtn.type = "button";
    editBtn.className = "history-link";
    editBtn.textContent = "Edit";

    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "history-link history-delete";
    deleteBtn.textContent = "Delete";

    const detail = document.createElement("div");
    detail.className = "history-detail hidden";

    viewBtn.addEventListener("click", () => toggleSessionDetails(viewBtn, item.id, detail));
    editBtn.addEventListener("click", () => startEditingSession(item.id));
    deleteBtn.addEventListener("click", () => deleteHistorySession(item.id));

    actions.appendChild(viewBtn);
    actions.appendChild(editBtn);
    actions.appendChild(deleteBtn);

    row.appendChild(text);
    row.appendChild(actions);
    wrapper.appendChild(row);
    wrapper.appendChild(detail);
    list.appendChild(wrapper);
  });

  renderCalendar(items);
}

async function completeWorkout() {
  const payload = collectWorkout();
  const editingId = editingSessionId;
  const endpoint = editingId ? `/api/history/${editingId}` : "/api/complete";
  const method = editingId ? "PUT" : "POST";

  const res = await fetch(endpoint, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json();
    alert(err.error || "Failed to save workout");
    return;
  }

  if (editingId) {
    historyDetailCache.delete(editingId);
    editingSessionId = null;
    document.getElementById("finishBtn").textContent = "Finish";
  }

  await loadState();
  await loadHistory();
}

function workoutDetailToState(detail) {
  const exercises = [];
  const names = WORKOUT_EXERCISES[detail.workout] || [];

  names.forEach((name) => {
    const rows = detail.sets
      .filter((setRow) => setRow.exercise_name === name)
      .sort((a, b) => a.set_number - b.set_number);

    exercises.push({
      name,
      weight: rows.length ? rows[0].weight : 0,
      sets: rows.map((row) => row.completed_reps),
      notes: (detail.notes && detail.notes[name]) || "",
    });
  });

  return {
    workout: detail.workout,
    exercises,
  };
}

async function startEditingSession(sessionId) {
  let detail;
  try {
    detail = await getSessionDetail(sessionId);
  } catch (_err) {
    alert("Failed to load workout for editing.");
    return;
  }

  editingSessionId = sessionId;
  renderWorkout(workoutDetailToState(detail));
  document.getElementById("finishBtn").textContent = "Save Edit";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function deleteHistorySession(sessionId) {
  const confirmed = window.confirm("Delete this workout?");
  if (!confirmed) {
    return;
  }

  const res = await fetch(`/api/history/${sessionId}`, { method: "DELETE" });
  if (!res.ok) {
    alert("Failed to delete workout.");
    return;
  }

  historyDetailCache.delete(sessionId);
  if (editingSessionId === sessionId) {
    editingSessionId = null;
    document.getElementById("finishBtn").textContent = "Finish";
    await loadState();
  }
  await loadHistory();
}

function formatLb(value) {
  return Number(value).toFixed(2).replace(/\.00$/, "").replace(/(\.\d)0$/, "$1");
}

function getPlateRows() {
  const rows = [];
  document.querySelectorAll(".plate-row").forEach((rowEl) => {
    const weight = Number(rowEl.querySelector(".plate-weight").value || "0");
    const count = Number(rowEl.querySelector(".plate-count").value || "0");
    if (weight > 0 && count > 0) {
      rows.push({ weight, count });
    }
  });
  return rows;
}

function savePlateConfig() {
  const config = {
    targetWeight: document.getElementById("targetWeight").value,
    barWeight: document.getElementById("barWeight").value,
    plates: getPlateRows(),
  };
  localStorage.setItem("stronglifts_plate_config", JSON.stringify(config));
}

function addPlateRow(weight = "", count = "") {
  const tpl = document.getElementById("plateRowTemplate");
  const node = tpl.content.cloneNode(true);
  const row = node.querySelector(".plate-row");
  const wInput = node.querySelector(".plate-weight");
  const cInput = node.querySelector(".plate-count");
  const removeBtn = node.querySelector(".remove-plate");

  wInput.value = weight;
  cInput.value = count;

  const onChange = () => savePlateConfig();
  wInput.addEventListener("input", onChange);
  cInput.addEventListener("input", onChange);

  removeBtn.addEventListener("click", () => {
    row.remove();
    savePlateConfig();
  });

  document.getElementById("plateRows").appendChild(node);
}

function getBestPlateLoad(targetSideUnits, plateTypes) {
  let best = {
    usedUnits: -1,
    plateCount: Number.POSITIVE_INFINITY,
    picks: null,
  };

  function dfs(index, remainingUnits, usedUnits, plateCount, picks) {
    if (index === plateTypes.length) {
      if (
        usedUnits > best.usedUnits ||
        (usedUnits === best.usedUnits && plateCount < best.plateCount)
      ) {
        best = {
          usedUnits,
          plateCount,
          picks: [...picks],
        };
      }
      return;
    }

    const plate = plateTypes[index];
    const maxTake = Math.min(plate.pairs, Math.floor(remainingUnits / plate.units));

    for (let take = maxTake; take >= 0; take -= 1) {
      picks.push(take);
      dfs(
        index + 1,
        remainingUnits - take * plate.units,
        usedUnits + take * plate.units,
        plateCount + take,
        picks
      );
      picks.pop();
    }
  }

  dfs(0, targetSideUnits, 0, 0, []);
  return best;
}

function calculatePlates() {
  const target = Number(document.getElementById("targetWeight").value || "0");
  const bar = Number(document.getElementById("barWeight").value || "0");
  const resultEl = document.getElementById("plateResult");

  if (target <= 0 || bar < 0) {
    resultEl.textContent = "Enter a valid target total and bar weight.";
    return;
  }

  if (target < bar) {
    resultEl.textContent = "Target must be greater than or equal to bar weight.";
    return;
  }

  const rawRows = getPlateRows();
  if (rawRows.length === 0) {
    resultEl.textContent = "Add at least one plate size and count.";
    return;
  }

  const targetSideUnits = Math.round(((target - bar) / 2) * PLATE_SCALE);
  if (targetSideUnits < 0) {
    resultEl.textContent = "Target is below bar weight.";
    return;
  }

  const plateTypes = rawRows
    .map((p) => ({
      weight: p.weight,
      units: Math.round(p.weight * PLATE_SCALE),
      pairs: Math.floor(p.count / 2),
    }))
    .filter((p) => p.units > 0 && p.pairs > 0)
    .sort((a, b) => b.weight - a.weight);

  if (plateTypes.length === 0) {
    resultEl.textContent = "No usable plate pairs found. Counts must be at least 2 per size.";
    return;
  }

  const best = getBestPlateLoad(targetSideUnits, plateTypes);
  if (!best.picks) {
    resultEl.textContent = "Could not calculate with current inputs.";
    return;
  }

  const perSide = [];
  plateTypes.forEach((plate, idx) => {
    const countPerSide = best.picks[idx];
    if (countPerSide > 0) {
      perSide.push(`${formatLb(plate.weight)} x ${countPerSide}`);
    }
  });

  const loadedTotal = bar + (best.usedUnits * 2) / PLATE_SCALE;
  const exact = best.usedUnits === targetSideUnits;

  const summary = [
    `<div><strong>Per side:</strong> ${perSide.join(", ") || "No plates"}</div>`,
    `<div><strong>Total loaded:</strong> ${formatLb(loadedTotal)} lb</div>`,
  ];

  if (!exact) {
    summary.push(
      `<div><strong>Closest under target:</strong> short by ${formatLb(target - loadedTotal)} lb</div>`
    );
  }

  resultEl.innerHTML = summary.join("");
  savePlateConfig();
}

function initPlateCalculator() {
  const saved = localStorage.getItem("stronglifts_plate_config");
  let config = null;

  try {
    config = saved ? JSON.parse(saved) : null;
  } catch (_err) {
    config = null;
  }

  if (config?.targetWeight) {
    document.getElementById("targetWeight").value = config.targetWeight;
  }
  if (config?.barWeight) {
    document.getElementById("barWeight").value = config.barWeight;
  }

  if (config?.plates?.length) {
    config.plates.forEach((p) => addPlateRow(p.weight, p.count));
  } else {
    addPlateRow(45, 2);
    addPlateRow(25, 2);
    addPlateRow(10, 2);
    addPlateRow(5, 2);
    addPlateRow(2.5, 2);
  }

  document.getElementById("addPlateRow").addEventListener("click", () => addPlateRow("", ""));
  document.getElementById("calcPlates").addEventListener("click", calculatePlates);
  document.getElementById("targetWeight").addEventListener("input", savePlateConfig);
  document.getElementById("barWeight").addEventListener("input", savePlateConfig);

  calculatePlates();
}

function initPlateToggle() {
  const toggle = document.getElementById("togglePlates");
  const content = document.getElementById("plateContent");
  const saved = localStorage.getItem("stronglifts_plate_collapsed");
  const collapsed = saved === null ? true : saved === "1";

  if (collapsed) {
    content.classList.add("hidden");
    toggle.textContent = "Show";
  }

  toggle.addEventListener("click", () => {
    content.classList.toggle("hidden");
    const isHidden = content.classList.contains("hidden");
    toggle.textContent = isHidden ? "Show" : "Hide";
    localStorage.setItem("stronglifts_plate_collapsed", isHidden ? "1" : "0");
  });
}

document.getElementById("finishBtn").addEventListener("click", completeWorkout);

initPlateToggle();
initPlateCalculator();
loadState();
loadHistory();
