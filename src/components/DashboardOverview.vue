<template>
  <section class="section block">
    <div class="block__head">
      <p class="eyebrow">One project, two views</p>
      <h2>Project dashboard overview</h2>
    </div>

    <div class="panels">
      <div class="panel dash">
        <div class="panel-head dash__head dash__head--internal">
          <span class="tag tag--info">Internal</span>
          <h3>Firm dashboard</h3>
        </div>
        <ul>
          <li v-for="i in internalDashboard" :key="i">{{ i }}</li>
        </ul>
      </div>

      <div class="panel dash">
        <div class="panel-head dash__head dash__head--client">
          <span class="tag tag--ok">Client</span>
          <h3>Client dashboard</h3>
        </div>
        <ul>
          <li v-for="i in clientDashboard" :key="i">{{ i }}</li>
        </ul>
      </div>
    </div>

    <div class="panel timeline">
      <div class="panel-head">
        <h3>Example client view &mdash; project timeline</h3>
      </div>
      <ol class="timeline__rail">
        <li v-for="t in projectTimeline" :key="t.label" :class="['tl', `tl--${t.state}`]">
          <span class="tl__dot" aria-hidden="true"></span>
          <span class="tl__label">{{ t.label }}</span>
        </li>
      </ol>
      <div class="timeline__legend">
        <span><span class="lg lg--done"></span>Completed</span>
        <span><span class="lg lg--active"></span>In progress</span>
        <span><span class="lg lg--pending"></span>Pending</span>
        <span><span class="lg lg--delayed"></span>Delayed</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { internalDashboard, clientDashboard, projectTimeline } from '../data/roadmap.js'
</script>

<style scoped>
.block { padding: 20px 0; }
.block__head { margin-bottom: 16px; }
.block__head h2 { font-size: 1.3rem; margin-top: 4px; }

.panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.dash__head { gap: 10px; }
.dash__head h3 { font-size: 0.98rem; }
.dash ul {
  list-style: none;
  margin: 0;
  padding: 14px 20px 18px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 14px;
}
.dash li {
  font-size: 0.82rem;
  padding-left: 16px;
  position: relative;
  color: var(--ink);
}
.dash li::before {
  content: "";
  position: absolute; left: 0; top: 6px;
  width: 6px; height: 6px;
  background: var(--slate-2);
  border-radius: 50%;
}

.timeline { padding-bottom: 18px; }
.timeline__rail {
  list-style: none;
  margin: 0;
  padding: 22px 24px 10px;
  display: flex;
  gap: 4px;
  overflow-x: auto;
}
.tl {
  flex: 1;
  min-width: 92px;
  text-align: center;
  position: relative;
}
.tl::before {
  content: "";
  position: absolute;
  top: 8px; left: -50%; right: 50%;
  height: 2px;
  background: var(--line);
}
.tl:first-child::before { display: none; }
.tl--done::before { background: var(--ok); }
.tl--active::before { background: var(--ok); }
.tl__dot {
  display: block;
  width: 16px; height: 16px;
  margin: 0 auto 8px;
  border-radius: 50%;
  background: var(--paper-2);
  border: 2px solid var(--slate-2);
  position: relative;
  z-index: 1;
}
.tl--done .tl__dot { background: var(--ok); border-color: var(--ok); }
.tl--active .tl__dot { border-color: var(--info); box-shadow: 0 0 0 4px var(--info-bg); }
.tl--delayed .tl__dot { background: var(--alert); border-color: var(--alert); }
.tl__label { font-size: 0.68rem; color: var(--slate); line-height: 1.25; display: block; }
.tl--active .tl__label { color: var(--info); font-weight: 600; }

.timeline__legend {
  display: flex;
  gap: 18px;
  padding: 6px 24px 18px;
  font-size: 0.72rem;
  color: var(--slate);
}
.timeline__legend span { display: inline-flex; align-items: center; gap: 6px; }
.lg { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.lg--done { background: var(--ok); }
.lg--active { background: var(--info); }
.lg--pending { background: var(--slate-2); }
.lg--delayed { background: var(--alert); }

@media (max-width: 900px) {
  .panels { grid-template-columns: 1fr; }
  .dash ul { grid-template-columns: 1fr; }
}
</style>
