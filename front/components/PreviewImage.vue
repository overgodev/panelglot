<script setup lang="ts">
const props = defineProps<{
  file: File;
  result: Blob | null;
}>();

const imageUrl = ref<string | null>(null);

watchEffect((onCleanup) => {
  const objectUrl = URL.createObjectURL(props.result ?? props.file);
  imageUrl.value = objectUrl;
  onCleanup(() => URL.revokeObjectURL(objectUrl));
});
</script>

<template>
  <img
    :src="imageUrl ?? undefined"
    :alt="file.name"
    class="w-full h-full object-contain rounded-lg border border-gray-200"
  />
</template>
