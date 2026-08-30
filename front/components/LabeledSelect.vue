<script setup lang="ts">
type Option = { label: string; value: string };

defineProps<{
  id: string;
  label: string;
  title?: string;
  options: Option[];
}>();

const model = defineModel<string>({ required: true });
</script>

<template>
  <div class="flex flex-col gap-1">
    <label :for="id" class="text-xs font-medium" style="color: var(--color-text-secondary)">{{ label }}</label>
    <select
      :id="id"
      :title="title"
      v-model="model"
      class="field-input"
    >
      <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
    </select>
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
