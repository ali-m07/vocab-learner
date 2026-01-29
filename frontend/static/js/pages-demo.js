(() => {
  /** @typedef {{word: string, translation?: string, definition?: string, word_type?: string, examples?: string[]}} DemoWord */

  /** @type {DemoWord[]} */
  const WORDS = [
    {
      word: "abandon",
      translation: "leave behind",
      word_type: "verb",
      definition: "To leave a place, thing, or person, usually forever.",
      examples: ["They had to abandon the car in the snow."],
    },
    {
      word: "accurate",
      translation: "correct",
      word_type: "adjective",
      definition: "Free from errors; exact.",
      examples: ["The report is accurate and well sourced."],
    },
    {
      word: "benefit",
      translation: "advantage",
      word_type: "noun",
      definition: "A helpful or good effect, or something that helps.",
      examples: ["A major benefit of exercise is better sleep."],
    },
    {
      word: "commit",
      translation: "devote",
      word_type: "verb",
      definition: "To decide to use time/energy for something; to pledge.",
      examples: ["She committed to practicing every day."],
    },
    {
      word: "clarify",
      translation: "make clear",
      word_type: "verb",
      definition: "To make something easier to understand.",
      examples: ["Can you clarify what you mean by that?"],
    },
    {
      word: "curious",
      translation: "eager to know",
      word_type: "adjective",
      definition: "Interested in learning or knowing about something.",
      examples: ["He was curious about how it worked."],
    },
    {
      word: "efficient",
      translation: "productive",
      word_type: "adjective",
      definition: "Working well without wasting time or energy.",
      examples: ["This is an efficient way to study."],
    },
    {
      word: "focus",
      translation: "concentrate",
      word_type: "verb",
      definition: "To give attention to one thing.",
      examples: ["Try to focus for 10 minutes at a time."],
    },
  ];

  const els = {
    grid: document.getElementById("wordsGrid"),
    searchInput: document.getElementById("searchInput"),
    searchBtn: document.getElementById("searchBtn"),
    wordType: document.getElementById("wordTypeFilter"),
    demoCount: document.getElementById("demoCount"),
    toast: document.getElementById("toast"),
  };

  /** @param {string} text */
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text ?? "";
    return div.innerHTML;
  }

  /** @param {HTMLElement} card */
  function flipCard(card) {
    card.classList.toggle("flipped");
  }

  /** @param {DemoWord} w */
  function createWordCard(w) {
    const hasExamples = Array.isArray(w.examples) && w.examples.length > 0;
    return `
      <div class="word-card" data-word-type="${escapeHtml(w.word_type || "")}">
        <div class="word-front">
          <div class="word-english">${escapeHtml(w.word)}</div>
        </div>
        <div class="word-back">
          <div class="word-translation">${escapeHtml(w.translation || "")}</div>
          ${w.word_type ? `<div class="word-type-badge">${escapeHtml(w.word_type)}</div>` : ""}
          ${w.definition ? `<div class="word-definition">${escapeHtml(w.definition)}</div>` : ""}
          ${
            hasExamples
              ? `<div class="word-examples"><strong>Example:</strong><div class="example-item">${escapeHtml(
                  w.examples[0]
                )}</div></div>`
              : ""
          }
        </div>
      </div>
    `;
  }

  /** @param {DemoWord[]} list */
  function render(list) {
    if (!els.grid) return;
    els.grid.innerHTML = list.map(createWordCard).join("");
    els.grid.querySelectorAll(".word-card").forEach((card) => {
      card.addEventListener("click", () => flipCard(card));
    });
    if (els.demoCount) els.demoCount.textContent = String(list.length);
  }

  function applyFilters() {
    const q = (els.searchInput?.value || "").trim().toLowerCase();
    const t = (els.wordType?.value || "").trim().toLowerCase();
    const filtered = WORDS.filter((w) => {
      const matchesType = !t || (w.word_type || "").toLowerCase() === t;
      const matchesQuery =
        !q ||
        w.word.toLowerCase().includes(q) ||
        (w.translation || "").toLowerCase().includes(q) ||
        (w.definition || "").toLowerCase().includes(q);
      return matchesType && matchesQuery;
    });
    render(filtered);
  }

  function showToast(message) {
    if (!els.toast) return;
    els.toast.textContent = message;
    els.toast.className = "toast success show";
    window.setTimeout(() => els.toast.classList.remove("show"), 2500);
  }

  // Wire up
  els.searchBtn?.addEventListener("click", applyFilters);
  els.searchInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") applyFilters();
  });
  els.wordType?.addEventListener("change", applyFilters);

  render(WORDS);
  showToast("Loaded demo vocabulary. Run the backend for full features.");
})();

