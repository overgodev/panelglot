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
  <div class="flex flex-col">
    <label :for="id" class="mb-1 text-sm text-gray-700 font-medium">{{ label }}</label>
    <select
      :id="id"
      :title="title"
      v-model="model"
      class="w-full appearance-none border border-gray-300 rounded pl-3 pr-6 py-1 text-sm text-gray-700 focus:border-blue-500 focus:outline-none"
    >
      <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
    </select>
  </div>
</template>
