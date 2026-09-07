import { test, expect } from "@playwright/test";
import { openApp, dismissWelcomeScreen } from "./helpers";

// The fork is built with VITE_APP_DISABLE_PLUS=true — the Excalidraw+
// marketing UI must not be rendered anywhere.
test.describe("no Excalidraw+ marketing", () => {
  test("no plus banner in the app", async ({ page }) => {
    await openApp(page);
    await dismissWelcomeScreen(page);
    await expect(page.locator(".plus-banner")).toHaveCount(0);
    await expect(page.getByText("Excalidraw+", { exact: true })).toHaveCount(0);
  });

  test("welcome screen has no sign-up marketing", async ({ page }) => {
    await openApp(page);
    // Core entries remain, the "Sign up" marketing link is gone.
    await expect(
      page.locator(".welcome-screen-menu-item").filter({ hasText: "Live collaboration" }),
    ).toHaveCount(1);
    await expect(
      page.locator(".welcome-screen-menu-item").filter({ hasText: "Sign up" }),
    ).toHaveCount(0);
  });

  test("no link points at plus.excalidraw.com", async ({ page }) => {
    await openApp(page);
    await dismissWelcomeScreen(page);
    // Covers the banner, welcome screen, main menu and help dialog links
    // (wherever they would be rendered).
    const plusLinks = await page.evaluate(() =>
      [...document.querySelectorAll("a")].filter((a) =>
        (a.getAttribute("href") || "").includes("plus.excalidraw.com"),
      ).length,
    );
    expect(plusLinks).toBe(0);
  });
});
