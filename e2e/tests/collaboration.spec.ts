import { test, expect, type BrowserContext, type Page } from "@playwright/test";
import {
  SYNC_THRESHOLD_MS,
  canvasPixels,
  dismissWelcomeScreen,
  drawRectangle,
  joinRoom,
  openApp,
  startRoom,
  waitForCanvasChange,
  waitForWelcomeScreenGone,
  welcomeScreenGone,
} from "./helpers";

// Collaboration tests share the same deployed relay — run them serially
// to avoid cross-test interference.
test.describe.configure({ mode: "serial" });

async function newTabs(browser: import("@playwright/test").Browser): Promise<{
  ctx: BrowserContext;
  a: Page;
  b: Page;
}> {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  return { ctx, a: await ctx.newPage(), b: await ctx.newPage() };
}

test.describe("excalidraw-room collaboration", () => {
  test("tab B joins the room started by tab A", async ({ browser }) => {
    const { ctx, a, b } = await newTabs(browser);
    await openApp(a);
    const roomLink = await startRoom(a);
    expect(roomLink).toContain("#room=");

    await joinRoom(b, roomLink);
    await expect(b).toHaveURL(/#room=/);
    await ctx.close();
  });

  test("drawing on A becomes visible on B without any interaction", async ({ browser }) => {
    const { ctx, a, b } = await newTabs(browser);

    await openApp(a);
    const roomLink = await startRoom(a);
    await dismissWelcomeScreen(a); // keep B's welcome screen: regression scenario

    await joinRoom(b, roomLink);
    // B joined an empty room: wait for its welcome screen to render
    // (only shown for an empty scene, once the app finished loading).
    await b
      .locator(".welcome-screen-menu-item")
      .first()
      .waitFor({ state: "visible", timeout: SYNC_THRESHOLD_MS });
    const bEmptyPixels = await canvasPixels(b);

    // Regression for "drawings only appear after clicking the menu":
    // B must pick the shape up WITHOUT any interaction, within the
    // latency budget. No click/keypress on B happens between the draw
    // and these assertions.
    const t0 = Date.now();
    await drawRectangle(a);
    await waitForCanvasChange(b, bEmptyPixels, SYNC_THRESHOLD_MS);
    const elapsed = Date.now() - t0;
    console.log(`sync latency A->B: ${elapsed}ms`);

    // The scene on B must be non-empty — the welcome screen (which only
    // renders for empty scenes) must be gone without any interaction.
    expect(await welcomeScreenGone(b)).toBe(true);

    await ctx.close();
  });

  test("drawing on B becomes visible on A (both directions)", async ({ browser }) => {
    const { ctx, a, b } = await newTabs(browser);

    await openApp(a);
    const roomLink = await startRoom(a);
    await dismissWelcomeScreen(a);

    await joinRoom(b, roomLink);
    await dismissWelcomeScreen(b);
    const aEmptyPixels = await canvasPixels(a);

    const t0 = Date.now();
    await drawRectangle(b);
    await waitForCanvasChange(a, aEmptyPixels, SYNC_THRESHOLD_MS);
    const elapsed = Date.now() - t0;
    console.log(`sync latency B->A: ${elapsed}ms`);

    await ctx.close();
  });

  test("background tab catches up after regaining focus", async ({ browser }) => {
    // Models the manual report "drawings appear only after I click the
    // menu of the second window": browsers throttle hidden tabs' rAF,
    // so React defers the paint until the tab is focused again. The
    // integration must deliver the update promptly once focused.
    const { ctx, a, b } = await newTabs(browser);

    await openApp(a);
    const roomLink = await startRoom(a);
    await dismissWelcomeScreen(a);

    await joinRoom(b, roomLink);
    await dismissWelcomeScreen(b);

    // Background B: with A in front, B is a hidden tab.
    await a.bringToFront();
    const bHiddenPixels = await canvasPixels(b);
    await drawRectangle(a);
    await b.waitForTimeout(1500);
    const bWhileHidden = await canvasPixels(b);
    console.log(`appeared while tab hidden: ${!bWhileHidden.equals(bHiddenPixels)}`);

    // Regaining focus must flush the pending update promptly.
    await b.bringToFront();
    await waitForCanvasChange(b, bHiddenPixels, SYNC_THRESHOLD_MS);

    await ctx.close();
  });

  test("scene already present when joining an existing room", async ({ browser }) => {
    const { ctx, a, b } = await newTabs(browser);

    await openApp(a);
    const roomLink = await startRoom(a);
    await dismissWelcomeScreen(a);
    await drawRectangle(a);
    await expect
      .poll(async () => welcomeScreenGone(a), { timeout: SYNC_THRESHOLD_MS })
      .toBe(true);

    // B joins a room that already has content — the scene must arrive
    // without A drawing anything new.
    await joinRoom(b, roomLink);
    await waitForWelcomeScreenGone(b, SYNC_THRESHOLD_MS);

    await ctx.close();
  });
});
