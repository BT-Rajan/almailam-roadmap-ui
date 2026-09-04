<!--
  Purely decorative ambient glow sitting behind the glass panels/cards.
  Fixed + aria-hidden so it never affects layout, scroll height, or
  screen readers -- just gives the flat page background some depth to
  match the app's glassmorphism surfaces (mirrors JDK's AmbientBackground).
-->
<script setup lang="ts"></script>

<template>
  <div class="ambient-background" aria-hidden="true">
    <div
      class="ambient-background__blob bg-accent-500"
      style="top: -10rem; left: -8rem; width: 32rem; height: 32rem"
    />
    <div
      class="ambient-background__blob bg-primary-500"
      style="top: 20%; right: -10rem; width: 26rem; height: 26rem"
    />
    <div
      class="ambient-background__blob bg-accent-400"
      style="bottom: -8rem; left: 25%; width: 24rem; height: 24rem"
    />
    <div class="ambient-background__grain" />
  </div>
</template>
