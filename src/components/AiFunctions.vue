<template>
  <section class="section block">
    <div class="block__head">
      <p class="eyebrow">In the background</p>
      <h2>AI functions in Phase 1</h2>
    </div>
    <div class="grid">
      <article v-for="f in aiFunctions" :key="f.title" class="card">
        <h3>{{ f.title }}</h3>
        <p class="card__detail">{{ f.detail }}</p>
        <ul>
          <li v-for="i in f.items" :key="i">{{ i }}</li>
        </ul>
        <div class="flow">
          <span v-for="(step, idx) in f.flow" :key="step" class="flow__step">
            {{ step }}<span v-if="idx < f.flow.length - 1" class="flow__arrow">&rarr;</span>
          </span>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { aiFunctions } from '../data/roadmap.js'
</script>

<style scoped>
.block { padding: 34px 0 6px; }
.block__head { margin-bottom: 16px; }
.block__head h2 { font-size: 1.3rem; margin-top: 4px; }

.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.card {
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 18px;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.card h3 { font-size: 0.98rem; color: var(--ink); }
.card__detail { font-size: 0.8rem; color: var(--slate); line-height: 1.4; }
.card ul {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex: 1;
}
.card li {
  font-size: 0.78rem;
  padding-left: 14px;
  position: relative;
  color: var(--ink);
}
.card li::before {
  content: "\2022";
  color: var(--brass);
  position: absolute;
  left: 0;
}
.flow {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  color: var(--info);
  background: var(--info-bg);
  border-radius: var(--radius-sm);
  padding: 6px 10px;
  letter-spacing: 0.02em;
}
.flow__arrow { margin: 0 5px; color: var(--slate-2); }

@media (max-width: 1000px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .grid { grid-template-columns: 1fr; }
}
</style>
