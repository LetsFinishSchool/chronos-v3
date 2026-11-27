import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";

const WCAG_22_AA_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

export async function expectNoA11yViolations(page: Page): Promise<void> {
  const { violations } = await new AxeBuilder({ page }).withTags(WCAG_22_AA_TAGS).analyze();
  if (violations.length === 0) return;

  const report = violations
    .map((v) => {
      const elements = v.nodes.map((n) => `    ${n.target.join(" ")}`).join("\n");
      return `- ${v.id} (${v.impact ?? "unbekannt"}): ${v.help}\n${elements}`;
    })
    .join("\n");
  throw new Error(`${violations.length} Barrierefreiheitsverstöße (WCAG 2.2 AA):\n${report}`);
}
