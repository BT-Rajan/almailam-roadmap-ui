<template>
  <section class="section block">
    <div class="panel">
      <div class="panel-head">
        <h2>Document &amp; approval tracking</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Item</th>
              <th>Required for</th>
              <th>Responsible</th>
              <th>Status</th>
              <th>Due date</th>
              <th>Received</th>
              <th>Approved</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in documents" :key="d.item">
              <td class="strong">{{ d.item }}</td>
              <td>{{ d.requiredFor }}</td>
              <td>{{ d.responsible }}</td>
              <td><span :class="['tag', tagClass(d.status)]">{{ d.status }}</span></td>
              <td class="mono">{{ d.due }}</td>
              <td class="mono">{{ d.received }}</td>
              <td class="mono">{{ d.approved }}</td>
              <td class="muted">{{ d.note }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script setup>
import { documents } from '../data/roadmap.js'

function tagClass(status) {
  const s = status.toLowerCase()
  if (s === 'uploaded' || s === 'approved') return 'tag--ok'
  if (s === 'missing' || s === 'not started') return 'tag--alert'
  if (s === 'under review') return 'tag--info'
  return 'tag--pending'
}
</script>

<style scoped>
.block { padding: 20px 0; }
.table-wrap { overflow-x: auto; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}
th {
  text-align: left;
  font-family: var(--font-mono);
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--slate);
  padding: 10px 16px;
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
}
td {
  padding: 11px 16px;
  border-bottom: 1px solid var(--line);
  color: var(--ink);
  white-space: nowrap;
}
tbody tr:last-child td { border-bottom: none; }
tbody tr:hover { background: var(--paper); }
.strong { font-weight: 600; }
.mono { font-family: var(--font-mono); font-size: 0.76rem; color: var(--slate); }
.muted { color: var(--slate); }
</style>
