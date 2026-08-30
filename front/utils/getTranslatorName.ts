import type { TranslatorKey } from "~/types";

export function getTranslatorName(key: TranslatorKey): string {
  switch (key) {
    case "none":
      return "No Text";
    case "original":
      return "Original (no translation)";
    case "custom_openai":
      return "Custom Endpoint (LM Studio / Ollama)";
  }
}
