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
  <div class="flex flex-col">
    <label :for="id" class="mb-1 text-sm text-gray-700 font-medium">{{ label }}</label>
    <input
      :id="id"
      :title="title"
      type="number"
      :step="step"
      v-model.number="model"
      class="w-full appearance-none border border-gray-300 rounded px-3 py-1 text-sm text-gray-700 focus:border-blue-500 focus:outline-none"
    />
  </div>
</template>
