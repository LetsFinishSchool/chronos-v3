import { expect, test } from "@playwright/test";

test("Seitenwechsel setzt Fokus auf die Überschrift und sagt den Titel an", async ({ page }) => {
  await page.goto("/unbekannt");
  const notFound = page.getByRole("heading", { level: 1, name: "Seite nicht gefunden" });
  await expect(notFound).toBeVisible();
  await expect(notFound).not.toBeFocused();

  await page.getByRole("link", { name: "Zur Startseite" }).click();

  await expect(page).toHaveURL("/");
  await expect(page.getByRole("heading", { level: 1, name: "Chronos" })).toBeFocused();
  await expect(page.getByRole("status")).toHaveText("Chronos");
});
