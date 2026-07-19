<template>
  <section class="section block block--last">
    <div class="panel bf">
      <div class="panel-head">
        <h2>Key benefits</h2>
      </div>
      <ul class="bf__grid">
        <li v-for="b in benefits" :key="b">
          <span class="bf__mark" aria-hidden="true">&#10003;</span>
          <span>{{ b }}</span>
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { benefits } from '../data/roadmap.js'
</script>

<style scoped>
.block { padding: 20px 0; }
.block--last { padding-bottom: 48px; }
.bf__grid {
  list-style: none;
  margin: 0;
  padding: 16px 20px 20px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px 24px;
}
.bf__grid li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.86rem;
  color: var(--ink);
}
.bf__mark {
  flex: none;
  width: 22px; height: 22px;
  border-radius: 50%;
  background: var(--brass);
  color: var(--ink);
  font-size: 0.7rem;
  font-weight: 700;
  display: grid;
  place-items: center;
}
@media (max-width: 700px) {
  .bf__grid { grid-template-columns: 1fr; }
}
</style>
