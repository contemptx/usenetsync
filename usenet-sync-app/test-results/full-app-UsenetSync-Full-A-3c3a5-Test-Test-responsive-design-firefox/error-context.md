# Page snapshot

```yaml
- text: "[plugin:vite:import-analysis] Failed to resolve import \"@tauri-apps/api/tauri\" from \"src/lib/tauri.ts\". Does the file exist? /workspace/usenet-sync-app/src/lib/tauri.ts:1:23 1 | import { invoke } from \"@tauri-apps/api/tauri\"; | ^ 2 | import { listen } from \"@tauri-apps/api/event\"; 3 | export async function activateLicense(key) { at TransformPluginContext._formatLog (file:///workspace/usenet-sync-app/node_modules/vite/dist/node/chunks/dep-CMEinpL-.js:31553:43) at TransformPluginContext.error (file:///workspace/usenet-sync-app/node_modules/vite/dist/node/chunks/dep-CMEinpL-.js:31550:14) at normalizeUrl (file:///workspace/usenet-sync-app/node_modules/vite/dist/node/chunks/dep-CMEinpL-.js:30022:18) at process.processTicksAndRejections (node:internal/process/task_queues:105:5) at async file:///workspace/usenet-sync-app/node_modules/vite/dist/node/chunks/dep-CMEinpL-.js:30080:32 at async Promise.all (index 0) at async TransformPluginContext.transform (file:///workspace/usenet-sync-app/node_modules/vite/dist/node/chunks/dep-CMEinpL-.js:30048:4) at async EnvironmentPluginContainer.transform (file:///workspace/usenet-sync-app/node_modules/vite/dist/node/chunks/dep-CMEinpL-.js:31351:14) at async loadAndTransform (file:///workspace/usenet-sync-app/node_modules/vite/dist/node/chunks/dep-CMEinpL-.js:26438:26) at async viteTransformMiddleware (file:///workspace/usenet-sync-app/node_modules/vite/dist/node/chunks/dep-CMEinpL-.js:27523:20) Click outside, press Esc key, or fix the code to dismiss. You can also disable this overlay by setting"
- code: server.hmr.overlay
- text: to
- code: "false"
- text: in
- code: vite.config.ts
- text: .
```