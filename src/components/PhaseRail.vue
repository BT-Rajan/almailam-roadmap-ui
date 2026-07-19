<template>
  <section class="section rail">
    <div class="rail__track" role="list" aria-label="Phase 1 steps">
      <article v-for="p in phases" :key="p.n" class="stage" role="listitem">
        <div class="stage__num">{{ p.n }}</div>
        <h3>{{ p.title }}</h3>
        <p class="stage__sub">{{ p.subtitle }}</p>
        <ul>
          <li v-for="s in (p.steps || p.channels)" :key="s">{{ s }}</li>
        </ul>
      </article>

      <div class="rail__arrow" aria-hidden="true">&rarr;</div>

      <article class="stage stage--active" role="listitem">
        <div class="stage__num stage__num--live">&#9679;</div>
        <h3>{{ active.title }}</h3>
        <p class="stage__sub">{{ active.subtitle }}</p>
        <div class="stage__views">
          <div v-for="v in active.views" :key="v.label" class="stage__view">
            <strong>{{ v.label }}</strong>
            <span>{{ v.detail }}</span>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { phases, active } from '../data/roadmap.js'
</script>

<style scoped>
.rail { padding-top: 28px; padding-bottom: 8px; }
.rail__track {
  display: grid;
  grid-template-columns: repeat(4, 1fr) auto 1.1fr;
  gap: 14px;
  align-items: stretch;
  position: relative;
}
.rail__arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--brass);
  font-size: 1.3rem;
}
.stage {
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-top: 3px solid var(--ink);
  border-radius: var(--radius);
  padding: 16px 16px 14px;
  position: relative;
  box-shadow: var(--shadow-card);
}
.stage__num {
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 0.78rem;
  color: var(--ink);
  background: var(--brass-2);
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  margin-bottom: 10px;
}
.stage h3 {
  font-size: 0.98rem;
  margin-bottom: 2px;
}
.stage__sub {
  font-size: 0.78rem;
  color: var(--slate);
  margin-bottom: 10px;
}
.stage ul {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.stage li {
  font-size: 0.78rem;
  padding-left: 16px;
  position: relative;
  color: var(--ink);
}
.stage li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 6px;
  width: 7px;
  height: 7px;
  border-radius: 2px;
  background: var(--ok);
}

.stage--active {
  border-top-color: var(--brass);
  background: linear-gradient(180deg, var(--ink) 0%, var(--ink-2) 100%);
  color: #fff;
}
.stage--active h3 { color: #fff; }
.stage--active .stage__sub { color: #b9c1d6; }
.stage__num--live {
  background: var(--brass);
  color: var(--ink);
  animation: pulse 2.4s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(201,151,79,0.5); }
  50% { box-shadow: 0 0 0 6px rgba(201,151,79,0); }
}
.stage__views { display: flex; gap: 10px; }
.stage__view {
  flex: 1;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.stage__view strong { font-family: var(--font-display); font-size: 0.85rem; }
.stage__view span { font-size: 0.7rem; color: #c9d0e2; }

@media (max-width: 1100px) {
  .rail__track { grid-template-columns: 1fr; }
  .rail__arrow { transform: rotate(90deg); padding: 2px 0; }
}
</style>
