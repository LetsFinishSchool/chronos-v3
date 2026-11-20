/** Architekturregel (V-1 §9): Fachbereiche (src/domain) dürfen Kanäle (src/channels) weder importieren noch davon abhängen (auch nicht indirekt). */
module.exports = {
  forbidden: [
    {
      name: "fachbereiche-kennen-kanaele-nicht",
      comment: "src/domain darf src/channels nicht erreichen (direkt oder transitiv).",
      severity: "error",
      from: { path: "^src/domain" },
      to: { path: "^src/channels", reachable: true },
    },
  ],
  options: { tsConfig: { fileName: "tsconfig.json" }, doNotFollow: { path: "node_modules" }, exclude: { path: "\\.test\\.ts$" } },
};
