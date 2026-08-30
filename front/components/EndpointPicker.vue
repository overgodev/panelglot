<script setup lang="ts">
import type { CustomEndpoint, LlmServerType } from "~/types";
import { loadEndpoints, saveEndpoints } from "~/utils/localStorage";

const selected = defineModel<CustomEndpoint | null>("selected", { required: true });

const endpoints = ref<CustomEndpoint[]>([]);
const NEW_VALUE = "__new__";
const dropdownValue = ref<string>(NEW_VALUE);
const showForm = ref(false);

const draft = ref({ name: "", baseUrl: "", apiKey: "", model: "" });

// Connection-test state: the Model field only appears once this succeeds, so the user
// picks from models the endpoint actually has instead of guessing a name.
const probeState = ref<"idle" | "testing" | "connected" | "error">("idle");
const probeError = ref("");
const probedModels = ref<string[]>([]);
const probedServerType = ref<LlmServerType>("unknown");

// Load/unload lifecycle: shown whenever an endpoint is (re)selected or saved.
const lifecycle = ref<{ phase: "idle" | "unloading" | "loading" | "ready" | "error"; message: string }>({
  phase: "idle",
  message: "",
});
// The endpoint we believe is actually resident in the server's memory right now
// (this session only - we can't know what happened before this page loaded).
const activeEndpoint = ref<CustomEndpoint | null>(null);

const persist = () => saveEndpoints(endpoints.value);

const resetDraft = () => {
  draft.value = { name: "", baseUrl: "", apiKey: "", model: "" };
  probeState.value = "idle";
  probeError.value = "";
  probedModels.value = [];
  probedServerType.value = "unknown";
};

onMounted(() => {
  endpoints.value = loadEndpoints();
  // Prefer the last-verified endpoint (one that has actually worked before);
  // fall back to whatever was saved most recently. Just select it - don't
  // spend network calls warming it up until the user actually does something.
  const preferred = [...endpoints.value].sort((a, b) => Number(b.verified) - Number(a.verified))[0] ?? null;
  if (preferred) {
    dropdownValue.value = preferred.id;
    selected.value = preferred;
  } else {
    dropdownValue.value = NEW_VALUE;
    showForm.value = true;
  }
});

const testConnection = async () => {
  if (!draft.value.baseUrl.trim()) return;
  probeState.value = "testing";
  probeError.value = "";
  try {
    const res = await $fetch<{ ok: boolean; server_type: LlmServerType; models: string[]; error?: string }>(
      "/api/llm/probe",
      { method: "POST", body: { base_url: draft.value.baseUrl.trim(), api_key: draft.value.apiKey.trim() || null } }
    );
    if (res.ok) {
      probedModels.value = res.models;
      probedServerType.value = res.server_type;
      draft.value.model = res.models[0] ?? "";
      probeState.value = "connected";
    } else {
      probeError.value = res.error || "Connection failed";
      probeState.value = "error";
    }
  } catch (err) {
    probeError.value = err instanceof Error ? err.message : "Connection failed";
    probeState.value = "error";
  }
};

const activateEndpoint = async (ep: CustomEndpoint) => {
  const prev = activeEndpoint.value;
  if (prev && (prev.baseUrl !== ep.baseUrl || prev.model !== ep.model)) {
    lifecycle.value = { phase: "unloading", message: `Unloading ${prev.model}…` };
    try {
      await $fetch("/api/llm/unload", {
        method: "POST",
        body: { base_url: prev.baseUrl, model: prev.model, server_type: prev.serverType },
      });
    } catch {
      // Non-fatal - some servers (LM Studio) have no remote unload API at all.
    }
  }

  lifecycle.value = { phase: "loading", message: `Loading ${ep.model || "model"}… first load can take a while` };
  try {
    const res = await $fetch<{ ok: boolean; latency_ms?: number; error?: string }>("/api/llm/warmup", {
      method: "POST",
      body: { base_url: ep.baseUrl, api_key: ep.apiKey || null, model: ep.model },
    });
    if (res.ok) {
      lifecycle.value = { phase: "ready", message: `${ep.model} ready (${res.latency_ms}ms)` };
      activeEndpoint.value = ep;
      endpoints.value = endpoints.value.map((e) =>
        e.id === ep.id ? { ...e, verified: true, lastUsedAt: new Date().toISOString() } : e
      );
      persist();
      if (selected.value?.id === ep.id) selected.value = endpoints.value.find((e) => e.id === ep.id) ?? null;
      setTimeout(() => {
        if (lifecycle.value.phase === "ready") lifecycle.value = { phase: "idle", message: "" };
      }, 3000);
    } else {
      lifecycle.value = { phase: "error", message: res.error || "Failed to load model" };
    }
  } catch (err) {
    lifecycle.value = { phase: "error", message: err instanceof Error ? err.message : "Failed to load model" };
  }
};

const onDropdownChange = () => {
  if (dropdownValue.value === NEW_VALUE) {
    resetDraft();
    showForm.value = true;
    selected.value = null;
    return;
  }
  const found = endpoints.value.find((e) => e.id === dropdownValue.value) ?? null;
  selected.value = found;
  showForm.value = false;
  if (found) activateEndpoint(found);
};

const saveDraft = async () => {
  if (probeState.value !== "connected" || !draft.value.model) return;
  const endpoint: CustomEndpoint = {
    id: `endpoint-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    name: draft.value.name.trim() || draft.value.baseUrl.trim(),
    baseUrl: draft.value.baseUrl.trim(),
    model: draft.value.model,
    apiKey: draft.value.apiKey.trim(),
    serverType: probedServerType.value,
    verified: false,
    lastUsedAt: null,
  };
  endpoints.value = [...endpoints.value, endpoint];
  persist();
  dropdownValue.value = endpoint.id;
  selected.value = endpoint;
  showForm.value = false;
  resetDraft();
  await activateEndpoint(endpoint);
};

const removeSelected = () => {
  if (!selected.value) return;
  endpoints.value = endpoints.value.filter((e) => e.id !== selected.value!.id);
  persist();
  if (activeEndpoint.value?.id === selected.value.id) activeEndpoint.value = null;
  selected.value = null;
  dropdownValue.value = NEW_VALUE;
  resetDraft();
  showForm.value = true;
};

// Called by the parent after a real translation using this endpoint finishes -
// an extra confirmation on top of the warm-up check above.
const markVerified = () => {
  if (!selected.value) return;
  endpoints.value = endpoints.value.map((e) =>
    e.id === selected.value!.id ? { ...e, verified: true, lastUsedAt: new Date().toISOString() } : e
  );
  persist();
  selected.value = endpoints.value.find((e) => e.id === selected.value!.id) ?? null;
};

defineExpose({ markVerified });
</script>

<template>
  <div class="flex flex-col gap-2">
    <div class="flex flex-col gap-1">
      <label class="text-xs font-medium" style="color: var(--color-text-secondary)">Endpoint</label>
      <div class="flex items-center gap-1.5">
        <select v-model="dropdownValue" class="field-select flex-1" @change="onDropdownChange">
          <option v-for="e in endpoints" :key="e.id" :value="e.id">
            {{ e.verified ? "✓ " : "" }}{{ e.name }}
          </option>
          <option :value="NEW_VALUE">+ Add new endpoint…</option>
        </select>
        <button
          v-if="selected"
          type="button"
          title="Remove this saved endpoint"
          class="w-7 h-7 flex items-center justify-center rounded shrink-0 transition-colors"
          style="color: var(--color-text-tertiary)"
          @click="removeSelected"
        >
          <Icon name="trash" :size="14" />
        </button>
      </div>
      <p v-if="selected" class="text-[11px] font-mono truncate" style="color: var(--color-text-tertiary)">
        {{ selected.baseUrl }} · {{ selected.model }}
      </p>
    </div>

    <div
      v-if="lifecycle.phase !== 'idle'"
      class="flex items-center gap-2 px-2.5 py-2 rounded-md text-[11px]"
      :style="{
        background:
          lifecycle.phase === 'error'
            ? 'var(--color-danger-soft)'
            : lifecycle.phase === 'ready'
              ? 'rgba(61, 214, 140, 0.12)'
              : 'var(--color-surface-sunken)',
        border: '1px solid ' + (lifecycle.phase === 'error' ? 'var(--color-danger)' : 'var(--color-border)'),
        color:
          lifecycle.phase === 'error'
            ? 'var(--color-danger)'
            : lifecycle.phase === 'ready'
              ? 'var(--color-success)'
              : 'var(--color-text-secondary)',
      }"
    >
      <span
        v-if="lifecycle.phase === 'unloading' || lifecycle.phase === 'loading'"
        class="w-3 h-3 rounded-full border-2 animate-spin shrink-0"
        style="border-color: var(--color-accent); border-top-color: transparent"
      />
      <Icon v-else-if="lifecycle.phase === 'ready'" name="check" :size="13" class="shrink-0" />
      <Icon v-else-if="lifecycle.phase === 'error'" name="alert" :size="13" class="shrink-0" />
      <span class="truncate">{{ lifecycle.message }}</span>
    </div>

    <div
      v-if="showForm"
      class="flex flex-col gap-2 p-2.5 rounded-md"
      style="background: var(--color-surface-sunken); border: 1px solid var(--color-border)"
    >
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium" style="color: var(--color-text-secondary)">Name</label>
        <input
          v-model="draft.name"
          type="text"
          name="endpoint-name"
          autocomplete="off"
          data-1p-ignore
          data-lpignore="true"
          placeholder="e.g. Home PC — LM Studio"
          class="field-input"
        />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium" style="color: var(--color-text-secondary)">IP / Host to hit</label>
        <div class="flex items-center gap-1.5">
          <input
            v-model="draft.baseUrl"
            type="text"
            name="endpoint-base-url"
            autocomplete="off"
            data-1p-ignore
            data-lpignore="true"
            placeholder="http://192.168.1.20:1234/v1"
            class="field-input font-mono flex-1"
            @keydown.enter.prevent="testConnection"
          />
        </div>
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium" style="color: var(--color-text-secondary)">
          Auth Token <span style="color: var(--color-text-tertiary)">(optional — leave blank for local servers)</span>
        </label>
        <input
          v-model="draft.apiKey"
          type="password"
          name="endpoint-token"
          autocomplete="new-password"
          data-1p-ignore
          data-lpignore="true"
          class="field-input font-mono"
        />
      </div>

      <button
        type="button"
        class="test-btn"
        :disabled="!draft.baseUrl.trim() || probeState === 'testing'"
        @click="testConnection"
      >
        <span
          v-if="probeState === 'testing'"
          class="w-3 h-3 rounded-full border-2 animate-spin shrink-0"
          style="border-color: currentColor; border-top-color: transparent"
        />
        {{ probeState === "testing" ? "Testing connection…" : "Test Connection" }}
      </button>

      <p v-if="probeState === 'error'" class="text-[11px]" style="color: var(--color-danger)">{{ probeError }}</p>
      <p v-if="probeState === 'connected'" class="text-[11px]" style="color: var(--color-success)">
        Connected — {{ probedServerType === "ollama" ? "Ollama" : "OpenAI-compatible" }} server,
        {{ probedModels.length }} model{{ probedModels.length === 1 ? "" : "s" }} found.
      </p>

      <div v-if="probeState === 'connected'" class="flex flex-col gap-1">
        <label class="text-xs font-medium" style="color: var(--color-text-secondary)">Model</label>
        <select v-model="draft.model" class="field-select">
          <option v-for="m in probedModels" :key="m" :value="m">{{ m }}</option>
        </select>
      </div>

      <button
        v-if="probeState === 'connected'"
        type="button"
        class="save-btn"
        :disabled="!draft.model"
        @click="saveDraft"
      >
        Save Endpoint
      </button>
    </div>
  </div>
</template>

<style scoped>
.field-select,
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

.field-select:focus,
.field-input:focus {
  border-color: var(--color-accent);
  outline: none;
}

.test-btn,
.save-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 10px;
  font-size: 12.5px;
  font-weight: 600;
  border-radius: var(--radius-sm);
  transition: background-color 120ms ease, opacity 120ms ease, color 120ms ease;
}

.test-btn {
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.test-btn:hover:not(:disabled) {
  border-color: var(--color-border-strong);
  background: var(--color-surface-raised);
}

.save-btn {
  color: #17110a;
  background: var(--color-accent);
}

.save-btn:hover:not(:disabled) {
  background: var(--color-accent-strong);
}

.test-btn:disabled,
.save-btn:disabled {
  opacity: 0.4;
}
</style>
