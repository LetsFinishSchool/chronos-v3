self.addEventListener("push", (event) => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) { data = { event_type: "unlesbar" }; }
  event.waitUntil(self.registration.showNotification("Chronos Spike", { body: (data.event_type || "?") + " " + (data.event_id || "") }));
});
