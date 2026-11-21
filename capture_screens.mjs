import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9222;
const ARTIFACT_DIR = "C:\\Users\\user\\.gemini\\antigravity\\brain\\2de0010a-3fd3-4a31-950d-ac0bd3d04363";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function getPageWsUrl() {
  for (let i = 0; i < 20; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      if (res.ok) {
        const list = await res.json();
        const page = list.find((item) => item.type === "page");
        if (page && page.webSocketDebuggerUrl) {
          return page.webSocketDebuggerUrl;
        }
      }
    } catch {}
    await sleep(500);
  }
  throw new Error("Could not find page target in Chrome");
}

async function run() {
  console.log("Launching Chrome CDP...");
  const chrome = spawn(
    CHROME_PATH,
    [
      "--headless=new",
      "--no-sandbox",
      "--disable-gpu",
      `--remote-debugging-port=${PORT}`,
      `--user-data-dir=C:\\Users\\user\\AppData\\Local\\Temp\\chrome_cdp_${Date.now()}`,
      "--window-size=1440,900",
      "about:blank",
    ],
    { stdio: "ignore" }
  );

  try {
    const wsUrl = await getPageWsUrl();
    console.log("Connected to Page target:", wsUrl);

    const ws = new WebSocket(wsUrl);
    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
    });

    let id = 1;
    function send(method, params = {}) {
      return new Promise((resolve, reject) => {
        const msgId = id++;
        const handler = (event) => {
          const res = JSON.parse(event.data);
          if (res.id === msgId) {
            ws.removeEventListener("message", handler);
            if (res.error) reject(res.error);
            else resolve(res.result);
          }
        };
        ws.addEventListener("message", handler);
        ws.send(JSON.stringify({ id: msgId, method, params }));
      });
    }

    await send("Page.enable");

    // 1. Desktop Pass (1440x900, deviceScaleFactor 2)
    await send("Emulation.setDeviceMetricsOverride", {
      width: 1440,
      height: 900,
      deviceScaleFactor: 2,
      mobile: false,
    });

    const routes = [
      { name: "dashboard", url: "http://localhost:3000/dashboard" },
      { name: "landing", url: "http://localhost:3000/" },
      { name: "inspection", url: "http://localhost:3000/inspection" },
      { name: "requirements", url: "http://localhost:3000/requirements" },
      { name: "comparison", url: "http://localhost:3000/comparison" },
      { name: "audit-history", url: "http://localhost:3000/audit-history" },
      { name: "settings", url: "http://localhost:3000/settings" },
    ];

    fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

    for (const route of routes) {
      console.log(`[Desktop] Navigating to ${route.url}...`);
      await send("Page.navigate", { url: route.url });
      await sleep(2200);

      const { data } = await send("Page.captureScreenshot", {
        format: "png",
        captureBeyondViewport: false,
      });

      const outPath = path.join(ARTIFACT_DIR, `${route.name}.png`);
      fs.writeFileSync(outPath, Buffer.from(data, "base64"));
      console.log(`Captured: ${route.name}.png (${(data.length * 0.75 / 1024).toFixed(0)} KB)`);
    }

    // 2. Mobile Pass (390x844 iPhone-class, deviceScaleFactor 2)
    console.log("Switching to Mobile Emulation (390x844)...");
    await send("Emulation.setDeviceMetricsOverride", {
      width: 390,
      height: 844,
      deviceScaleFactor: 2,
      mobile: true,
    });

    const mobileRoutes = [
      { name: "mobile-dashboard", url: "http://localhost:3000/dashboard" },
      { name: "mobile-inspection", url: "http://localhost:3000/inspection" },
    ];

    for (const route of mobileRoutes) {
      console.log(`[Mobile] Navigating to ${route.url}...`);
      await send("Page.navigate", { url: route.url });
      await sleep(2200);

      const { data } = await send("Page.captureScreenshot", {
        format: "png",
        captureBeyondViewport: false,
      });

      const outPath = path.join(ARTIFACT_DIR, `${route.name}.png`);
      fs.writeFileSync(outPath, Buffer.from(data, "base64"));
      console.log(`Captured: ${route.name}.png (${(data.length * 0.75 / 1024).toFixed(0)} KB)`);
    }

    ws.close();
    console.log("All desktop and mobile screenshots captured successfully!");
  } finally {
    chrome.kill();
  }
}

run().catch((err) => {
  console.error("Capture failed:", err);
  process.exit(1);
});
