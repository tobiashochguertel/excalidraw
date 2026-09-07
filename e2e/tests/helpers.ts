import type { Page } from "@playwright/test";

// The deployed self-hosted stack. Overridable for other environments.
export const BASE_URL = process.env.EXCALIDRAW_URL ?? "http://localhost:44186";

// Maximum acceptable delay between drawing on one tab and the scene
// becoming visible on the other. Loopback should be well under 1s; the
// threshold catches "long delay" regressions.
export const SYNC_THRESHOLD_MS = Number(
  process.env.EXCALIDRAW_SYNC_THRESHOLD_MS ?? 3000,
);

// This Excalidraw version paints the scene onto a <canvas> (no SVG
// shapes in the DOM), so "scene has content" is detected via:
// 1. canvas pixel comparison, and
// 2. the welcome screen — it only renders while the scene is empty
//    (App.tsx: renderWelcomeScreen requires !scene.length), so it
//    disappearing without interaction proves a re-render happened.
export const EMPTY_SCENE_HINT = "Pick a tool & Start drawing!";

export async function openApp(page: Page): Promise<void> {
  await page.goto(BASE_URL);
  await page.locator(".excalidraw").first().waitFor({ state: "visible" });
}

export async function welcomeScreenIsVisible(page: Page): Promise<boolean> {
  return (await page.locator(".welcome-screen-menu-item").count()) > 0;
}

export async function dismissWelcomeScreen(page: Page): Promise<void> {
  if (await welcomeScreenIsVisible(page)) {
    await page.locator(".welcome-screen-menu-item").first().click();
  }
}

export async function startRoom(page: Page): Promise<string> {
  await page
    .locator(".welcome-screen-menu-item", { hasText: "Live collaboration" })
    .click();
  await page.locator(".ShareDialog__picker__button button").click();
  await page.waitForFunction(() => location.hash.startsWith("#room="));
  const link = BASE_URL + (await page.evaluate(() => location.hash));
  await closeShareDialog(page);
  return link;
}

// The share dialog (room link, "Stop session") has no close button; it
// is dismissed with Escape or by clicking the modal background. It must
// be closed — its overlay would otherwise swallow canvas clicks.
export async function closeShareDialog(page: Page): Promise<void> {
  await page.keyboard.press("Escape");
  const dialog = page.locator(".ShareDialog");
  try {
    await dialog.waitFor({ state: "hidden", timeout: 3000 });
  } catch {
    await page.mouse.click(10, 10);
    await dialog.waitFor({ state: "hidden", timeout: 3000 });
  }
}

export async function joinRoom(page: Page, roomLink: string): Promise<void> {
  await page.goto(roomLink);
  await page.locator(".excalidraw").first().waitFor({ state: "visible" });
}

export async function drawRectangle(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Rectangle", exact: true }).first().click();
  await page.mouse.move(500, 400);
  await page.mouse.down();
  await page.mouse.move(850, 650, { steps: 10 });
  await page.mouse.up();
}

// PNG of the painted scene canvas — proves a shape is actually painted.
export async function canvasPixels(page: Page): Promise<Buffer> {
  return page.locator(".excalidraw__canvas.static").screenshot();
}

// Polls the canvas until its pixels differ from the baseline. Throws if
// unchanged within timeoutMs — the latency/regression assertion.
export async function waitForCanvasChange(
  page: Page,
  baseline: Buffer,
  timeoutMs: number,
): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const current = await canvasPixels(page);
    if (!current.equals(baseline)) return;
    await page.waitForTimeout(300);
  }
  throw new Error(`canvas did not change within ${timeoutMs}ms`);
}

// True once the welcome screen is gone — i.e. the scene has content and
// the UI re-rendered (the welcome screen only renders for empty scenes).
export async function welcomeScreenGone(page: Page): Promise<boolean> {
  return (await page.locator(".welcome-screen-menu-item").count()) === 0;
}

// Waits until the welcome screen disappears without any interaction.
export async function waitForWelcomeScreenGone(page: Page, timeoutMs: number): Promise<void> {
  await page.waitForFunction(
    () => document.querySelectorAll(".welcome-screen-menu-item").length === 0,
    { timeout: timeoutMs },
  );
}
