<script setup lang="ts">
import type { SavedStory } from "~/types";

const stories = ref<SavedStory[]>([]);

onMounted(() => {
  stories.value = loadStories();
});

const openStory = (id: string) => navigateTo({ path: "/", query: { openStory: id } });

const removeStory = (id: string) => {
  stories.value = deleteStory(id);
};

const thumbFor = (story: SavedStory): string | null => {
  const first = story.pages[0];
  return first ? first.resultDataUrl ?? first.imageDataUrl : null;
};

const formatDate = (iso: string) => new Date(iso).toLocaleString();
</script>

<template>
  <div class="h-screen flex flex-col overflow-hidden">
    <header
      class="flex items-center gap-4 h-14 px-4 border-b shrink-0"
      style="background: var(--color-surface); border-color: var(--color-border)"
    >
      <NuxtLink to="/" class="flex items-center gap-2.5 shrink-0" style="color: var(--color-text)">
        <Icon name="chevron-down" :size="16" class="rotate-90" style="color: var(--color-text-secondary)" />
        <Icon name="book" :size="19" style="color: var(--color-accent)" />
        <span class="font-semibold tracking-tight text-[15px]" style="font-family: var(--font-display)">
          Panelglot
        </span>
      </NuxtLink>
      <div class="h-5 w-px shrink-0" style="background: var(--color-border)" />
      <h1 class="text-sm font-medium" style="color: var(--color-text-secondary)">Stories</h1>
    </header>

    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="stories.length === 0" class="h-full flex flex-col items-center justify-center gap-3">
        <Icon name="layers" :size="28" style="color: var(--color-text-tertiary)" />
        <div class="text-center">
          <p class="text-sm" style="color: var(--color-text)">No saved stories yet</p>
          <p class="text-xs mt-1" style="color: var(--color-text-tertiary)">
            Use "Save as Story" from the workspace to keep a project here and start a new one.
          </p>
        </div>
        <NuxtLink to="/" class="text-xs font-medium mt-1" style="color: var(--color-accent)">
          Back to workspace
        </NuxtLink>
      </div>

      <div v-else class="grid gap-4" style="grid-template-columns: repeat(auto-fill, minmax(200px, 1fr))">
        <div
          v-for="story in stories"
          :key="story.id"
          class="rounded-lg overflow-hidden flex flex-col cursor-pointer group transition-colors"
          style="background: var(--color-surface); border: 1px solid var(--color-border)"
          @click="openStory(story.id)"
        >
          <div class="aspect-[3/4] relative overflow-hidden" style="background: var(--color-surface-sunken)">
            <img
              v-if="thumbFor(story)"
              :src="thumbFor(story)!"
              :alt="story.name"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
            />
            <div v-else class="w-full h-full flex items-center justify-center">
              <Icon name="image" :size="24" style="color: var(--color-text-tertiary)" />
            </div>

            <button
              type="button"
              title="Delete story"
              class="absolute top-2 right-2 w-7 h-7 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
              style="background: rgba(10, 10, 12, 0.7); color: var(--color-text)"
              @click.stop="removeStory(story.id)"
            >
              <Icon name="trash" :size="13" />
            </button>
          </div>

          <div class="p-3 flex flex-col gap-0.5">
            <div class="text-sm font-medium truncate" style="color: var(--color-text)">{{ story.name }}</div>
            <div class="text-[11px]" style="color: var(--color-text-tertiary)">
              {{ story.pages.length }} page{{ story.pages.length === 1 ? "" : "s" }} · {{ formatDate(story.createdAt) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
