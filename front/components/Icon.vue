<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    name:
      | "pointer"
      | "pan"
      | "lasso"
      | "zoom-in"
      | "zoom-out"
      | "upload"
      | "download"
      | "trash"
      | "close"
      | "check"
      | "alert"
      | "image"
      | "chevron-down"
      | "plus"
      | "layers"
      | "book";
    size?: number;
  }>(),
  { size: 18 }
);

const paths: Record<typeof props.name, string> = {
  pointer: '<path d="M5 3v17l4.5-4 2.5 5.5 2.4-1.1L12 15h5.5L5 3Z" />',
  pan: '<path d="M12 2v20M2 12h20M5 9l-3 3 3 3M19 9l3 3-3 3M9 5l3-3 3 3M9 19l3 3 3-3" />',
  lasso:
    '<ellipse cx="12" cy="10.5" rx="8" ry="6.2" stroke-dasharray="2.2 3" /><circle cx="9" cy="18.2" r="1.4" fill="currentColor" stroke="none" />',
  "zoom-in":
    '<circle cx="11" cy="11" r="7" /><path d="M11 8v6M8 11h6" /><path d="M16.4 16.4 21 21" />',
  "zoom-out": '<circle cx="11" cy="11" r="7" /><path d="M8 11h6" /><path d="M16.4 16.4 21 21" />',
  upload: '<path d="M12 3v12" /><path d="M7 8l5-5 5 5" /><path d="M4 21h16" />',
  download: '<path d="M12 3v12" /><path d="M7 10l5 5 5-5" /><path d="M4 21h16" />',
  trash: '<path d="M4 7h16" /><path d="M9 7V4h6v3" /><path d="M6 7l1 13h10l1-13" />',
  close: '<path d="M5 5l14 14" /><path d="M19 5 5 19" />',
  check: '<path d="M4 12l5 5L20 6" />',
  alert:
    '<path d="M12 3 22 20H2Z" /><path d="M12 9.5v4.2" /><circle cx="12" cy="17" r="0.6" fill="currentColor" stroke="none" />',
  image:
    '<rect x="3" y="4" width="18" height="16" rx="2.2" /><circle cx="8.5" cy="9.5" r="1.4" /><path d="M3.8 16.5 9 11.2l3.6 3.6 2.6-2.6 5 4.7" />',
  "chevron-down": '<path d="M6 9l6 6 6-6" />',
  plus: '<path d="M12 5v14" /><path d="M5 12h14" />',
  layers:
    '<path d="M12 3 3 8l9 5 9-5-9-5Z" /><path d="M3 12l9 5 9-5" /><path d="M3 16l9 5 9-5" />',
  book: '<path d="M4 4.5c2-1 5-1 8 0v15c-3-1-6-1-8 0v-15Z" /><path d="M20 4.5c-2-1-5-1-8 0v15c3-1 6-1 8 0v-15Z" />',
};
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.75"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    v-html="paths[name]"
  />
</template>
