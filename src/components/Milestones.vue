<template>
  <section class="section block">
    <div class="panel ms">
      <div class="panel-head">
        <h2>Typical project milestones <span class="muted">(example)</span></h2>
      </div>
      <ol class="ms__grid">
        <li v-for="(m, idx) in milestones" :key="m">
          <span class="ms__num">{{ idx + 1 }}</span>
          <span>{{ m }}</span>
        </li>
      </ol>
    </div>
  </section>
</template>

<script setup>
import { milestones } from '../data/roadmap.js'
</script>

<style scoped>
.block { padding: 20px 0; }
.muted { color: var(--slate); font-weight: 400; font-size: 0.85rem; }
.ms__grid {
  list-style: none;
  margin: 0;
  padding: 16px 20px 20px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px 20px;
}
.ms__grid li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.85rem;
}
.ms__num {
  flex: none;
  width: 24px; height: 24px;
  border-radius: 50%;
  background: var(--ink);
  color: var(--brass-2);
  font-family: var(--font-mono);
  font-size: 0.7rem;
  font-weight: 700;
  display: grid;
  place-items: center;
}
@media (max-width: 800px) {
  .ms__grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 500px) {
  .ms__grid { grid-template-columns: 1fr; }
}
</style>
