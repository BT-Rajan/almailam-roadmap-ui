<template>
  <section class="section block">
    <div class="panel config">
      <div class="panel-head config__head">
        <span class="dot" aria-hidden="true"></span>
        <h2>Service based configuration</h2>
      </div>
      <p class="config__lede">Every service has its own setup</p>

      <div class="config__cols">
        <div class="config__col">
          <p class="col__label">Examples of services</p>
          <ul class="tick-list">
            <li v-for="s in serviceExamples" :key="s">{{ s }}</li>
          </ul>
        </div>
        <div class="config__col">
          <p class="col__label">For each service, define</p>
          <ul class="field-list">
            <li v-for="f in serviceFields" :key="f.label">{{ f.label }}</li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { serviceExamples, serviceFields } from '../data/roadmap.js'
</script>

<style scoped>
.block { padding: 20px 0; }
.config { padding: 18px 20px 22px; }
.config__head { padding: 0 0 10px; border: none; }
.config__head h2 { font-size: 1.15rem; }
.dot {
  width: 9px; height: 9px; border-radius: 50%;
  background: var(--ok);
}
.config__lede { color: var(--slate); font-size: 0.85rem; margin-bottom: 16px; }

.config__cols {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 24px;
}
.col__label {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--slate);
  margin-bottom: 10px;
}
.tick-list, .field-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 16px;
}
.tick-list li, .field-list li {
  font-size: 0.82rem;
  padding-left: 20px;
  position: relative;
  color: var(--ink);
}
.tick-list li::before {
  content: "";
  position: absolute; left: 0; top: 5px;
  width: 10px; height: 6px;
  border-left: 2px solid var(--ok);
  border-bottom: 2px solid var(--ok);
  transform: rotate(-45deg);
}
.field-list { grid-template-columns: 1fr; }
.field-list li::before {
  content: "";
  position: absolute; left: 0; top: 6px;
  width: 8px; height: 8px;
  background: var(--brass);
  border-radius: 2px;
}

@media (max-width: 800px) {
  .config__cols { grid-template-columns: 1fr; }
}
</style>
