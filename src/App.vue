<template>
  <div class="app">
    <AppHeader />
    <main>
      <PhaseRail />
      <AiFunctions />
      <ServiceConfig />
      <DashboardOverview />
      <DocumentTracking />
      <Milestones />
      <Benefits />
    </main>
    <footer class="footer">
      <div class="section footer__row">
        <span>Abdulhadi Almailem Engineering Consulting Firm</span>
        <span class="footer__muted">Phase 1 clickable mockup &mdash; front end only, no live data</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import AppHeader from './components/AppHeader.vue'
import PhaseRail from './components/PhaseRail.vue'
import AiFunctions from './components/AiFunctions.vue'
import ServiceConfig from './components/ServiceConfig.vue'
import DashboardOverview from './components/DashboardOverview.vue'
import DocumentTracking from './components/DocumentTracking.vue'
import Milestones from './components/Milestones.vue'
import Benefits from './components/Benefits.vue'
</script>

<style scoped>
.app { min-height: 100vh; display: flex; flex-direction: column; }
main { flex: 1; }
.footer {
  border-top: 1px solid var(--line);
  padding: 16px 0 28px;
}
.footer__row {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 0.75rem;
  color: var(--slate);
}
</style>
