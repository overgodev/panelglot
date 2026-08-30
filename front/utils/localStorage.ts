import type { TranslationSettings, FinishedImage, StoryContext, CustomEndpoint, SavedStory } from "~/types";
import { blobToDataUrl, dataUrlToBlob } from "./blob";

const SETTINGS_KEY = "manga-translator-settings";
const FINISHED_IMAGES_KEY = "manga-translator-finished-images";
const STORY_CONTEXT_KEY = "manga-translator-story-context";
const ENDPOINTS_KEY = "manga-translator-endpoints";
const STORIES_KEY = "manga-translator-stories";

type StoredFinishedImage = Omit<FinishedImage, "result" | "finishedAt"> & { result: string; finishedAt: string };

export const loadSettings = (): Partial<TranslationSettings> => {
  try {
    const stored = localStorage.getItem(SETTINGS_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch (error) {
    console.warn("Failed to load settings from localStorage:", error);
    return {};
  }
};

export const saveSettings = (settings: TranslationSettings): void => {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch (error) {
    console.warn("Failed to save settings to localStorage:", error);
  }
};

export const loadFinishedImages = (): FinishedImage[] => {
  try {
    const stored = localStorage.getItem(FINISHED_IMAGES_KEY);
    if (!stored) return [];
    const parsed: StoredFinishedImage[] = JSON.parse(stored);
    return parsed.map((img) => ({ ...img, result: dataUrlToBlob(img.result), finishedAt: new Date(img.finishedAt) }));
  } catch (error) {
    console.warn("Failed to load finished images from localStorage:", error);
    return [];
  }
};

export const saveFinishedImages = async (images: FinishedImage[]): Promise<void> => {
  try {
    // Blobs don't survive JSON.stringify (they serialize to "{}") - encode as data URLs.
    // Keep only the most recent 50 to prevent localStorage from getting too large.
    const limitedImages = images.slice(0, 50);
    const serializable: StoredFinishedImage[] = await Promise.all(
      limitedImages.map(async (img) => ({
        ...img,
        result: await blobToDataUrl(img.result),
        finishedAt: img.finishedAt.toISOString(),
      }))
    );
    localStorage.setItem(FINISHED_IMAGES_KEY, JSON.stringify(serializable));
  } catch (error) {
    console.warn("Failed to save finished images to localStorage:", error);
  }
};

export const loadStoryContext = (): Partial<StoryContext> => {
  try {
    const stored = localStorage.getItem(STORY_CONTEXT_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch (error) {
    console.warn("Failed to load story context from localStorage:", error);
    return {};
  }
};

export const saveStoryContext = (context: StoryContext): void => {
  try {
    localStorage.setItem(STORY_CONTEXT_KEY, JSON.stringify(context));
  } catch (error) {
    console.warn("Failed to save story context to localStorage:", error);
  }
};

export const loadEndpoints = (): CustomEndpoint[] => {
  try {
    const stored = localStorage.getItem(ENDPOINTS_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.warn("Failed to load endpoints from localStorage:", error);
    return [];
  }
};

export const saveEndpoints = (endpoints: CustomEndpoint[]): void => {
  try {
    localStorage.setItem(ENDPOINTS_KEY, JSON.stringify(endpoints));
  } catch (error) {
    console.warn("Failed to save endpoints to localStorage:", error);
  }
};

export const addFinishedImage = async (image: FinishedImage): Promise<void> => {
  try {
    const existing = loadFinishedImages();
    const updated = [image, ...existing]; // Add new image at the top
    await saveFinishedImages(updated);
  } catch (error) {
    console.warn("Failed to add finished image to localStorage:", error);
  }
};

export const loadStories = (): SavedStory[] => {
  try {
    const stored = localStorage.getItem(STORIES_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.warn("Failed to load stories from localStorage:", error);
    return [];
  }
};

export const saveStories = (stories: SavedStory[]): void => {
  try {
    localStorage.setItem(STORIES_KEY, JSON.stringify(stories));
  } catch (error) {
    console.warn("Failed to save stories to localStorage:", error);
  }
};

export const deleteStory = (id: string): SavedStory[] => {
  const remaining = loadStories().filter((story) => story.id !== id);
  saveStories(remaining);
  return remaining;
};
