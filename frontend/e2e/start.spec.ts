import { expect, test } from "@playwright/test";

test("Startseite zeigt die Überschrift", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: "Chronos" })).toBeVisible();
});
