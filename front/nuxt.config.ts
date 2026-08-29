export default defineNuxtConfig({
  compatibilityDate: "2024-11-01",
  devtools: { enabled: false },
  modules: ["@nuxtjs/tailwindcss"],
  css: ["~/assets/css/main.css"],

  app: {
    head: {
      title: "Manga/Webtoon Translator",
      meta: [{ name: "description", content: "Manga/Webtoon Translator" }],
    },
  },

  // Forward /api/* to the panelglot backend during dev and in production.
  routeRules: {
    "/api/**": { proxy: "http://localhost:8000/**" },
  },
});
