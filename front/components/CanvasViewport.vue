<script setup lang="ts">
import type { FileStatus, ManualBox, OcrPreviewRegion } from "~/types";

const props = defineProps<{
  file: File | null;
  result: Blob | null;
  status: FileStatus | null;
  zoom: number;
  tool: "pointer" | "pan" | "lasso";
  manualBoxes: ManualBox[];
  previewRegions: OcrPreviewRegion[] | null;
  extraError?: string | null;
}>();

const emit = defineEmits<{
  (e: "drop", event: DragEvent): void;
  (e: "file-change", event: Event): void;
  (e: "add-manual-box", box: ManualBox): void;
  (e: "remove-manual-box", index: number): void;
}>();

const imageUrl = ref<string | null>(null);
watchEffect((onCleanup) => {
  if (!props.file) {
    imageUrl.value = null;
    return;
  }
  const url = URL.createObjectURL(props.result ?? props.file);
  imageUrl.value = url;
  onCleanup(() => URL.revokeObjectURL(url));
});

const naturalWidth = ref(0);
const naturalHeight = ref(0);
const onImgLoad = (e: Event) => {
  const img = e.target as HTMLImageElement;
  naturalWidth.value = img.naturalWidth;
  naturalHeight.value = img.naturalHeight;
};
watch(imageUrl, () => {
  naturalWidth.value = 0;
  naturalHeight.value = 0;
});

const svgRef = ref<SVGSVGElement | null>(null);

const pan = ref({ x: 0, y: 0 });
const dragging = ref(false);
const dragStart = { x: 0, y: 0, panX: 0, panY: 0 };

// Converts a screen point (pointer event clientX/Y) into the SVG's own viewBox space
// (natural image pixels). getScreenCTM bakes in every ancestor CSS transform - the pan/zoom
// transform on the outer wrapper included - so this stays correct at any zoom/pan state
// without any manual math.
const clientToImagePoint = (clientX: number, clientY: number): { x: number; y: number } | null => {
  const svg = svgRef.value;
  if (!svg) return null;
  const ctm = svg.getScreenCTM();
  if (!ctm) return null;
  const pt = svg.createSVGPoint();
  pt.x = clientX;
  pt.y = clientY;
  const transformed = pt.matrixTransform(ctm.inverse());
  return { x: transformed.x, y: transformed.y };
};

const dragBox = ref<{ x: number; y: number; w: number; h: number } | null>(null);
let boxStart: { x: number; y: number } | null = null;

const onPointerDown = (e: PointerEvent) => {
  if (props.tool === "pan") {
    dragging.value = true;
    dragStart.x = e.clientX;
    dragStart.y = e.clientY;
    dragStart.panX = pan.value.x;
    dragStart.panY = pan.value.y;
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  } else if (props.tool === "lasso") {
    const pt = clientToImagePoint(e.clientX, e.clientY);
    if (!pt) return;
    boxStart = pt;
    dragBox.value = { x: pt.x, y: pt.y, w: 0, h: 0 };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }
};
const onPointerMove = (e: PointerEvent) => {
  if (dragging.value) {
    pan.value = {
      x: dragStart.panX + (e.clientX - dragStart.x),
      y: dragStart.panY + (e.clientY - dragStart.y),
    };
  } else if (boxStart) {
    const pt = clientToImagePoint(e.clientX, e.clientY);
    if (!pt) return;
    dragBox.value = {
      x: Math.min(boxStart.x, pt.x),
      y: Math.min(boxStart.y, pt.y),
      w: Math.abs(pt.x - boxStart.x),
      h: Math.abs(pt.y - boxStart.y),
    };
  }
};
const onPointerUp = () => {
  dragging.value = false;
  if (dragBox.value && boxStart) {
    const { x, y, w, h } = dragBox.value;
    // Minimum ~10 image-px in each axis so a stray click doesn't register as a box.
    if (w > 10 && h > 10) {
      const box: ManualBox = [x, y, x + w, y, x + w, y + h, x, y + h].map((n) => Math.round(n));
      emit("add-manual-box", box);
    }
  }
  boxStart = null;
  dragBox.value = null;
};

watch(
  () => props.zoom,
  () => {
    pan.value = { x: 0, y: 0 };
  }
);

const manualRects = computed(() =>
  props.manualBoxes.map((box) => {
    const xs = [box[0], box[2], box[4], box[6]];
    const ys = [box[1], box[3], box[5], box[7]];
    const x = Math.min(...xs);
    const y = Math.min(...ys);
    return { x, y, w: Math.max(...xs) - x, h: Math.max(...ys) - y };
  })
);

const isBusy = computed(() => props.status && props.status.status && props.status.status !== "finished");
</script>

<template>
  <div
    class="relative flex-1 min-w-0 flex items-center justify-center overflow-hidden"
    @dragover.prevent
    @dragenter.prevent
    @drop.prevent="emit('drop', $event)"
  >
    <div
      class="absolute inset-0"
      style="
        background-image: linear-gradient(var(--color-border) 1px, transparent 1px),
          linear-gradient(90deg, var(--color-border) 1px, transparent 1px);
        background-size: 28px 28px;
        opacity: 0.1;
      "
    />

    <template v-if="file">
      <!--
        Absolutely-positioned insets give this box a DEFINITE height (root minus fixed
        insets). A plain block here would have height:auto, and percentage/max-height on
        the <img> can't resolve against an auto-height ancestor - it silently falls back to
        unconstrained, so a tall source page rendered at native size with the rest clipped
        and nothing to scroll it into view with. inset-8 fixes that at any resolution.
      -->
      <div
        class="absolute inset-8 select-none"
        :class="{
          'cursor-grab': tool === 'pan' && !dragging,
          'cursor-grabbing': tool === 'pan' && dragging,
          'cursor-crosshair': tool === 'lasso',
        }"
        :style="{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: 'center',
          transition: dragging ? 'none' : 'transform 120ms ease',
        }"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointerleave="onPointerUp"
      >
        <!--
          Both the <img> and the <svg> overlay fill this SAME definite-sized box (inset-0
          against the already-definite inset-8 above) and letterbox independently within it -
          object-contain for the img, preserveAspectRatio="xMidYMid meet" for the svg. Same
          source aspect ratio into the same box means they land pixel-identically, and
          getScreenCTM below already accounts for that letterboxing automatically.
        -->
        <img
          :src="imageUrl ?? undefined"
          :alt="file.name"
          class="absolute inset-0 w-full h-full object-contain rounded-sm shadow-[var(--shadow-pop)] pointer-events-none"
          draggable="false"
          @load="onImgLoad"
        />

        <svg
          v-if="naturalWidth"
          ref="svgRef"
          class="absolute inset-0 w-full h-full pointer-events-none"
          :viewBox="`0 0 ${naturalWidth} ${naturalHeight}`"
          preserveAspectRatio="xMidYMid meet"
        >
            <rect
              v-for="(r, i) in manualRects"
              :key="'manual-' + i"
              :x="r.x"
              :y="r.y"
              :width="r.w"
              :height="r.h"
              fill="rgba(246, 130, 31, 0.15)"
              stroke="#f6821f"
              stroke-width="3"
              vector-effect="non-scaling-stroke"
              :style="{ pointerEvents: tool === 'lasso' ? 'auto' : 'none', cursor: tool === 'lasso' ? 'pointer' : undefined }"
              @click="emit('remove-manual-box', i)"
            >
              <title>Manually marked text — click to remove</title>
            </rect>

            <g v-for="(r, i) in previewRegions ?? []" :key="'preview-' + i">
              <rect
                :x="r.minX"
                :y="r.minY"
                :width="r.maxX - r.minX"
                :height="r.maxY - r.minY"
                fill="rgba(61, 214, 140, 0.12)"
                stroke="#3dd68c"
                stroke-width="3"
                vector-effect="non-scaling-stroke"
              >
                <title>{{ r.text || "(no text recognized)" }}</title>
              </rect>
            </g>

            <rect
              v-if="dragBox"
              :x="dragBox.x"
              :y="dragBox.y"
              :width="dragBox.w"
              :height="dragBox.h"
              fill="rgba(246, 130, 31, 0.2)"
              stroke="#f6821f"
              stroke-width="3"
              stroke-dasharray="10 6"
              vector-effect="non-scaling-stroke"
            />
        </svg>
      </div>

      <div
        v-if="isBusy"
        class="absolute inset-0 flex items-center justify-center"
        style="background: rgba(10, 10, 12, 0.72)"
      >
        <div
          class="px-5 py-3 rounded-md text-sm font-medium flex items-center gap-2.5"
          style="background: var(--color-surface); border: 1px solid var(--color-border); color: var(--color-text)"
        >
          <span
            class="w-3.5 h-3.5 rounded-full border-2 animate-spin shrink-0"
            style="border-color: var(--color-accent); border-top-color: transparent"
          />
          {{ fetchStatusText(status!.status, status!.progress, status!.queuePos, status!.error) }}
        </div>
      </div>

      <div
        v-if="status?.error"
        class="absolute top-4 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 rounded-md text-sm"
        style="background: var(--color-danger-soft); color: var(--color-danger); border: 1px solid var(--color-danger)"
      >
        <Icon name="alert" :size="15" />
        {{ status.error }}
      </div>

      <div
        v-if="extraError"
        class="absolute top-4 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 rounded-md text-sm"
        style="background: var(--color-danger-soft); color: var(--color-danger); border: 1px solid var(--color-danger)"
      >
        <Icon name="alert" :size="15" />
        {{ extraError }}
      </div>

      <div
        v-if="tool === 'lasso'"
        class="absolute bottom-4 left-1/2 -translate-x-1/2 px-3 py-1.5 rounded-full text-xs"
        style="background: var(--color-surface); border: 1px solid var(--color-border); color: var(--color-text-secondary)"
      >
        Drag a box around text the detector missed
      </div>
    </template>

    <label
      v-else
      for="canvas-file-input"
      class="relative z-10 flex flex-col items-center gap-3 px-12 py-10 rounded-lg border border-dashed cursor-pointer transition-colors"
      style="border-color: var(--color-border-strong); color: var(--color-text-secondary)"
    >
      <Icon name="image" :size="28" style="color: var(--color-text-tertiary)" />
      <div class="text-center text-sm">
        <div style="color: var(--color-text)">Drop pages here</div>
        <div class="mt-0.5" style="color: var(--color-text-tertiary)">or click to select images</div>
      </div>
      <input
        id="canvas-file-input"
        type="file"
        multiple
        accept="image/png,image/jpeg,image/bmp,image/webp"
        class="hidden"
        @change="emit('file-change', $event)"
      />
    </label>
  </div>
</template>
