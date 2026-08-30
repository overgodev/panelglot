<script setup lang="ts">
const props = defineProps<{
  open: boolean;
  defaultName: string;
  pageCount: number;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "confirm", name: string): void;
}>();

const name = ref(props.defaultName);
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) name.value = props.defaultName || "Untitled Story";
  }
);

const confirm = () => emit("confirm", name.value.trim() || "Untitled Story");
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 flex items-center justify-center z-50"
    style="background: rgba(10, 10, 12, 0.75)"
    @click.self="emit('close')"
  >
    <div
      class="w-[360px] rounded-lg p-5 flex flex-col gap-4"
      style="background: var(--color-surface); border: 1px solid var(--color-border); box-shadow: var(--shadow-pop)"
    >
      <div>
        <h2 class="text-[15px] font-semibold" style="font-family: var(--font-display); color: var(--color-text)">
          Save as Story
        </h2>
        <p class="text-xs mt-1" style="color: var(--color-text-tertiary)">
          Saves these {{ pageCount }} page{{ pageCount === 1 ? "" : "s" }} as a story you can reopen later, then
          clears the canvas to start a new one.
        </p>
      </div>

      <div class="flex flex-col gap-1">
        <label for="story-name" class="text-xs font-medium" style="color: var(--color-text-secondary)">
          Story Name
        </label>
        <input
          id="story-name"
          v-model="name"
          type="text"
          autocomplete="off"
          class="field-input"
          @keydown.enter="confirm"
        />
      </div>

      <div class="flex justify-end gap-2">
        <button type="button" class="btn-ghost" @click="emit('close')">Cancel</button>
        <button type="button" class="btn-accent" @click="confirm">Save Story</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.field-input {
  width: 100%;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface-sunken);
  color: var(--color-text);
  padding: 7px 10px;
  font-size: 13px;
}

.field-input:focus {
  border-color: var(--color-accent);
  outline: none;
}

.btn-ghost {
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 500;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}

.btn-ghost:hover {
  color: var(--color-text);
  background: var(--color-surface-raised);
}

.btn-accent {
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 600;
  border-radius: var(--radius-md);
  color: #17110a;
  background: var(--color-accent);
}

.btn-accent:hover {
  background: var(--color-accent-strong);
}
</style>
