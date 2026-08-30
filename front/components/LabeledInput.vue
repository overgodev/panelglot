<script setup lang="ts">
defineProps<{
  id: string;
  label: string;
  title?: string;
  step?: number | string;
}>();

const model = defineModel<number>({ required: true });
</script>

<template>
  <div class="flex flex-col gap-1">
    <label :for="id" class="text-xs font-medium" style="color: var(--color-text-secondary)">{{ label }}</label>
    <input
      :id="id"
      :title="title"
      type="number"
      :step="step"
      v-model.number="model"
      class="field-input font-mono"
    />
  </div>
</template>

<style scoped>
.field-input {
  width: 100%;
  appearance: none;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface-sunken);
  color: var(--color-text);
  padding: 6px 10px;
  font-size: 13px;
  transition: border-color 120ms ease;
}

.field-input:focus {
  border-color: var(--color-accent);
  outline: none;
}
</style>
