// Wrapper for Tauri API to handle environments where it's not available

import { invoke as tauriInvoke } from '@tauri-apps/api/core';
import { listen as tauriListen } from '@tauri-apps/api/event';

export const invoke = tauriInvoke;
export const listen = tauriListen;
