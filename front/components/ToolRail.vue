<script setup lang="ts">
const tool = defineModel<"pointer" | "pan" | "lasso">("tool", { required: true });
const zoom = defineModel<number>("zoom", { required: true });

const emit = defineEmits<{ (e: "upload-click"): void }>();

const setTool = (next: "pointer" | "pan" | "lasso") => {
  tool.value = next;
};

const zoomBy = (delta: number) => {
  zoom.value = Math.min(4, Math.max(0.25, Number((zoom.value + delta).toFixed(2))));
};

const editingZoom = ref(false);
const zoomInput = ref("");
const zoomInputRef = ref<HTMLInputElement | null>(null);

const startEditingZoom = async () => {
  zoomInput.value = String(Math.round(zoom.value * 100));
  editingZoom.value = true;
  await nextTick();
  zoomInputRef.value?.focus();
  zoomInputRef.value?.select();
};

const applyZoomInput = () => {
  const parsed = Number(zoomInput.value);
  if (Number.isFinite(parsed) && parsed > 0) {
    zoom.value = Math.min(4, Math.max(0.25, parsed / 100));
  }
  editingZoom.value = false;
};

const cancelEditingZoom = () => {
  editingZoom.value = false;
};
</script>

<template>
  <div
    class="flex md:flex-col items-center gap-1 shrink-0 border-b md:border-b-0 md:border-r px-2 py-2 md:px-1.5 md:py-3"
    style="background: var(--color-surface); border-color: var(--color-border)"
  >
    <button
      type="button"
      title="Select"
      class="tool-btn"
      :class="{ active: tool === 'pointer' }"
      @click="setTool('pointer')"
    >
      <Icon name="pointer" :size="18" />
    </button>

    <button
      type="button"
      title="Pan"
      class="tool-btn"
      :class="{ active: tool === 'pan' }"
      @click="setTool('pan')"
    >
      <Icon name="pan" :size="18" />
    </button>

    <button
      type="button"
      title="Mark missed text — drag a box on the canvas"
      class="tool-btn"
      :class="{ active: tool === 'lasso' }"
      @click="setTool('lasso')"
    >
      <Icon name="lasso" :size="18" />
    </button>

    <div class="hidden md:block w-6 h-px my-1.5" style="background: var(--color-border)" />
    <div class="md:hidden h-6 w-px mx-1.5" style="background: var(--color-border)" />

    <button type="button" title="Zoom in" class="tool-btn" @click="zoomBy(0.25)">
      <Icon name="zoom-in" :size="18" />
    </button>

    <button type="button" title="Zoom out" class="tool-btn" @click="zoomBy(-0.25)">
      <Icon name="zoom-out" :size="18" />
    </button>

    <input
      v-if="editingZoom"
      ref="zoomInputRef"
      v-model="zoomInput"
      type="text"
      inputmode="numeric"
      class="hidden md:block w-9 text-[10px] font-mono tabular-nums text-center rounded-sm"
      style="background: var(--color-surface-sunken); border: 1px solid var(--color-accent); color: var(--color-text)"
      @blur="applyZoomInput"
      @keydown.enter="applyZoomInput"
      @keydown.escape="cancelEditingZoom"
    />
    <div
      v-else
      class="hidden md:block text-[10px] font-mono tabular-nums cursor-text"
      title="Double-click to type a zoom level"
      style="color: var(--color-text-tertiary)"
      @dblclick="startEditingZoom"
    >
      {{ Math.round(zoom * 100) }}%
    </div>

    <div class="flex-1" />

    <button type="button" title="Upload pages" class="tool-btn" @click="emit('upload-click')">
      <Icon name="upload" :size="18" />
    </button>
  </div>
</template>

<style scoped>
.tool-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  transition: background-color 120ms ease, color 120ms ease;
}

.tool-btn:hover:not(:disabled) {
  background: var(--color-surface-raised);
  color: var(--color-text);
}

.tool-btn.active {
  background: var(--color-accent-soft);
  color: var(--color-accent-strong);
}
</style>
