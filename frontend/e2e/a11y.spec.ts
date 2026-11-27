import { expect, test } from "@playwright/test";
import { expectNoA11yViolations } from "./support/axe";

test("Startseite hat keine Barrierefreiheitsverstöße", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expectNoA11yViolations(page);
});

test("Seite „nicht gefunden“ hat keine Barrierefreiheitsverstöße", async ({ page }) => {
  await page.goto("/unbekannt");
  await expect(page.getByRole("heading", { level: 1, name: "Seite nicht gefunden" })).toBeVisible();
  await expectNoA11yViolations(page);
});

test("Gegenprobe: Bild ohne alt lässt den axe-Baustein scheitern", async ({ page }) => {
  await page.goto("/");
  await page.evaluate(() => {
    const img = document.createElement("img");
    img.src = "data:image/gif;base64,R0lGODlhAQABAAAAACw=";
    document.body.append(img);
  });
  await expect(expectNoA11yViolations(page)).rejects.toThrow(/image-alt/);
});
