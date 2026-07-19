<template>
  <header class="header">
    <div class="section header__row">
      <div class="mark">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none" aria-hidden="true">
          <rect x="1" y="1" width="38" height="38" rx="8" stroke="#c9974f" stroke-width="1.5" />
          <path d="M11 29V15l9-6 9 6v14" stroke="#0f1f3d" stroke-width="1.6" stroke-linejoin="round" />
          <path d="M15 29v-8h10v8" stroke="#c9974f" stroke-width="1.6" stroke-linejoin="round" />
        </svg>
        <div class="mark__text">
          <strong>Abdulhadi Almailem</strong>
          <span>Engineering Consulting Firm</span>
        </div>
      </div>

      <div class="header__title">
        <p class="eyebrow">Phase 1 &mdash; From Request to Project Tracking</p>
        <h1>AI-Powered Workflow &amp; Dashboards</h1>
        <p class="header__sub">From first inquiry to municipality approval tracking</p>
      </div>

      <div class="assistant">
        <div class="assistant__icon">AI</div>
        <p><strong>AI Assistant</strong><br />Works in the background to save time, reduce errors and keep everyone informed.</p>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  background: var(--paper-2);
  border-bottom: 1px solid var(--line);
  padding: 22px 0;
}
.header__row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 28px;
  align-items: center;
}
.mark { display: flex; align-items: center; gap: 12px; }
.mark__text { display: flex; flex-direction: column; line-height: 1.25; }
.mark__text strong { font-family: var(--font-display); font-size: 0.95rem; }
.mark__text span { font-size: 0.72rem; color: var(--slate); }

.header__title { text-align: center; }
.header__title h1 {
  font-size: clamp(1.3rem, 2.4vw, 1.9rem);
  margin: 4px 0 2px;
}
.header__sub { color: var(--slate); font-size: 0.9rem; }

.assistant {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--ink);
  color: #fff;
  border-radius: var(--radius);
  padding: 10px 14px;
  max-width: 260px;
}
.assistant p { font-size: 0.72rem; line-height: 1.35; color: #cfd6e6; }
.assistant p strong { color: #fff; font-family: var(--font-display); font-size: 0.8rem; }
.assistant__icon {
  flex: none;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: var(--brass);
  color: var(--ink);
  display: grid;
  place-items: center;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 0.72rem;
}

@media (max-width: 900px) {
  .header__row { grid-template-columns: 1fr; text-align: center; justify-items: center; }
  .assistant { max-width: 100%; }
}
</style>
