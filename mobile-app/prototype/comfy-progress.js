// WebSocket progress helper for ComfyUI prototype.
// Uses ComfyUI's /ws endpoint with a browser-side client id.

let comfyProgressSocket = null;
let comfyProgressClientId = null;
let comfyProgressPromptId = null;
let comfyProgressHandler = null;

function getProgressClientId() {
  if (comfyProgressClientId) return comfyProgressClientId;
  comfyProgressClientId = 'mobile_' + Math.random().toString(16).slice(2) + '_' + Date.now();
  return comfyProgressClientId;
}

function joinUrlPath(basePath, childPath) {
  const left = basePath.endsWith('/') ? basePath.slice(0, -1) : basePath;
  const right = childPath.startsWith('/') ? childPath.slice(1) : childPath;
  if (!left || left === '/') return '/' + right;
  return left + '/' + right;
}

function toWebSocketUrl(httpBaseUrl) {
  const url = new URL(httpBaseUrl);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.pathname = joinUrlPath(url.pathname, '/ws');
  url.searchParams.set('clientId', getProgressClientId());
  return url.toString();
}

function connectComfyProgress(httpBaseUrl, onMessage) {
  closeComfyProgress();
  comfyProgressHandler = onMessage;
  const wsUrl = toWebSocketUrl(httpBaseUrl);
  comfyProgressSocket = new WebSocket(wsUrl);

  comfyProgressSocket.onopen = () => {
    if (comfyProgressHandler) comfyProgressHandler({ type: 'socket_open', message: 'WebSocket connected' });
  };

  comfyProgressSocket.onclose = () => {
    if (comfyProgressHandler) comfyProgressHandler({ type: 'socket_close', message: 'WebSocket closed' });
  };

  comfyProgressSocket.onerror = () => {
    if (comfyProgressHandler) comfyProgressHandler({ type: 'socket_error', message: 'WebSocket error' });
  };

  comfyProgressSocket.onmessage = event => {
    if (typeof event.data !== 'string') return;
    let data;
    try {
      data = JSON.parse(event.data);
    } catch (e) {
      return;
    }
    if (comfyProgressHandler) comfyProgressHandler(data);
  };

  return getProgressClientId();
}

function closeComfyProgress() {
  if (comfyProgressSocket) {
    try { comfyProgressSocket.close(); } catch (e) {}
  }
  comfyProgressSocket = null;
  comfyProgressHandler = null;
  comfyProgressPromptId = null;
}

function setProgressPromptId(promptId) {
  comfyProgressPromptId = promptId;
}

function getProgressPromptId() {
  return comfyProgressPromptId;
}

function getPromptPayloadWithClientId(prompt) {
  return {
    prompt,
    client_id: getProgressClientId(),
  };
}

window.ComfyMobileProgress = {
  getProgressClientId,
  toWebSocketUrl,
  connectComfyProgress,
  closeComfyProgress,
  setProgressPromptId,
  getProgressPromptId,
  getPromptPayloadWithClientId,
};
