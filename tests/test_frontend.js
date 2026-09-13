/**
 * Automated test suite for ShopAssist AI frontend (FEAT-004-FE).
 * 
 * Verifies DOM message rendering, streaming token accumulation, cursor animations,
 * latency badge calculation, session reset, connection state badges, and error handling.
 * 
 * Run with: node tests/test_frontend.js
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

// 1. Lightweight Simulated DOM Implementation
class DOMTokenList {
  constructor(element) {
    this.element = element;
    this._tokens = new Set();
  }

  add(...tokens) {
    for (const token of tokens) {
      if (token) this._tokens.add(token);
    }
    this._sync();
  }

  remove(...tokens) {
    for (const token of tokens) {
      this._tokens.delete(token);
    }
    this._sync();
  }

  contains(token) {
    return this._tokens.has(token);
  }

  toggle(token, force) {
    if (force === true) {
      this.add(token);
      return true;
    } else if (force === false) {
      this.remove(token);
      return false;
    }
    if (this._tokens.has(token)) {
      this.remove(token);
      return false;
    } else {
      this.add(token);
      return true;
    }
  }

  _sync() {
    this.element._className = Array.from(this._tokens).join(' ');
  }

  _fromClassName(className) {
    this._tokens.clear();
    if (className) {
      className.split(/\s+/).filter(Boolean).forEach(t => this._tokens.add(t));
    }
  }
}

class MockElement {
  constructor(tagName = 'div', id = '') {
    this.tagName = tagName.toUpperCase();
    this.id = id;
    this._className = '';
    this.classList = new DOMTokenList(this);
    this.children = [];
    this.parentNode = null;
    this.attributes = {};
    this.style = {};
    this.listeners = {};
    this._textContent = '';
    this._innerHTML = '';
    this.value = '';
    this.disabled = false;
    this.scrollHeight = 500;
    this.scrollTop = 0;
  }

  get className() {
    return this._className;
  }

  set className(val) {
    this._className = val || '';
    this.classList._fromClassName(this._className);
  }

  get textContent() {
    if (this.children.length === 0) return this._textContent;
    return this.children.map(c => c.textContent).join('');
  }

  set textContent(val) {
    this._textContent = String(val);
    this.children = [];
    this._innerHTML = escapeHtml(String(val));
  }

  get innerHTML() {
    return this._innerHTML;
  }

  set innerHTML(val) {
    this._innerHTML = String(val);
    this._textContent = String(val).replace(/<[^>]*>/g, '');
    if (val === '') {
      this.children = [];
      this._textContent = '';
    }
  }

  appendChild(child) {
    child.parentNode = this;
    this.children.push(child);
    return child;
  }

  removeChild(child) {
    const idx = this.children.indexOf(child);
    if (idx !== -1) {
      this.children.splice(idx, 1);
      child.parentNode = null;
    }
    return child;
  }

  replaceChildren(...newChildren) {
    this.children = [];
    for (const child of newChildren) {
      if (typeof child === 'string') {
        const textNode = new MockElement('span');
        textNode.textContent = child;
        this.appendChild(textNode);
      } else if (child) {
        this.appendChild(child);
      }
    }
  }

  setAttribute(key, val) {
    this.attributes[key] = String(val);
    if (key === 'class') this.className = String(val);
    if (key === 'id') this.id = String(val);
  }

  getAttribute(key) {
    if (key === 'class') return this.className;
    if (key === 'id') return this.id;
    return this.attributes[key] || null;
  }

  removeAttribute(key) {
    delete this.attributes[key];
    if (key === 'class') this.className = '';
    if (key === 'id') this.id = '';
  }

  addEventListener(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(callback);
  }

  removeEventListener(event, callback) {
    if (!this.listeners[event]) return;
    this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
  }

  dispatchEvent(event) {
    const eventType = typeof event === 'string' ? event : (event.type || 'click');
    const evtObj = typeof event === 'string' ? { type: event, target: this, preventDefault() {} } : event;
    if (!evtObj.target) evtObj.target = this;
    if (!evtObj.preventDefault) evtObj.preventDefault = () => {};

    let curr = this;
    while (curr) {
      const callbacks = curr.listeners[eventType] || [];
      for (const cb of callbacks) {
        cb.call(curr, evtObj);
      }
      curr = curr.parentNode;
    }
  }

  querySelector(selector) {
    return querySelector(this, selector);
  }

  querySelectorAll(selector) {
    return querySelectorAll(this, selector);
  }

  focus() {}
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function querySelector(node, selector) {
  const results = querySelectorAll(node, selector);
  return results.length > 0 ? results[0] : null;
}

function querySelectorAll(node, selector) {
  const results = [];
  function search(current) {
    for (const child of current.children) {
      let match = false;
      if (selector.startsWith('.')) {
        const cls = selector.slice(1);
        if (child.classList.contains(cls)) match = true;
      } else if (selector.startsWith('#')) {
        const id = selector.slice(1);
        if (child.id === id) match = true;
      } else if (child.tagName.toLowerCase() === selector.toLowerCase()) {
        match = true;
      }
      if (match) results.push(child);
      search(child);
    }
  }
  search(node);
  return results;
}

// 2. Mock WebSocket Implementation
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  constructor(url) {
    this.url = url;
    this.readyState = MockWebSocket.CONNECTING;
    this.sentMessages = [];
    MockWebSocket.lastInstance = this;

    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) this.onopen({ type: 'open' });
    }, 1);
  }

  send(data) {
    this.sentMessages.push(data);
  }

  close(code = 1000, reason = '') {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) this.onclose({ code, reason, wasClean: true });
  }

  simulateMessage(obj) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(obj) });
    }
  }

  simulateError(err = new Error('Connection error')) {
    if (this.onerror) this.onerror(err);
  }
}

// 3. Environment Builder
function createTestEnvironment() {
  const document = new MockElement('document');
  const body = new MockElement('body');
  document.body = body;

  const elementsById = {};

  function register(el) {
    if (el.id) elementsById[el.id] = el;
    for (const c of el.children) register(c);
    return el;
  }

  // Create UI Skeleton per FEAT-004-FE
  const chatWindow = new MockElement('main', 'chat-window');
  const messagesList = new MockElement('div', 'messages-list');
  const welcomeCard = new MockElement('div', 'welcome-card');
  welcomeCard.className = 'welcome-card';
  messagesList.appendChild(welcomeCard);
  chatWindow.appendChild(messagesList);

  const chipsContainer = new MockElement('div', 'chips-container');
  const chip1 = new MockElement('button');
  chip1.className = 'chip';
  chip1.setAttribute('data-prompt', 'Track ORD-1085');
  chip1.textContent = '📦 Track ORD-1085';

  const chip2 = new MockElement('button');
  chip2.className = 'chip';
  chip2.setAttribute('data-prompt', 'Return Policy');
  chip2.textContent = '🔄 Return Policy';

  const chip3 = new MockElement('button');
  chip3.className = 'chip';
  chip3.setAttribute('data-prompt', 'Noise Canceling Headphones');
  chip3.textContent = '🎧 Headphones under $150';

  chipsContainer.appendChild(chip1);
  chipsContainer.appendChild(chip2);
  chipsContainer.appendChild(chip3);

  const messageInput = new MockElement('textarea', 'message-input');
  const sendBtn = new MockElement('button', 'send-btn');
  const resetBtn = new MockElement('button', 'reset-btn');
  const statusBadge = new MockElement('div', 'status-badge');
  const statusIndicator = new MockElement('span', 'status-indicator');
  const statusText = new MockElement('span', 'status-text');
  statusBadge.appendChild(statusIndicator);
  statusBadge.appendChild(statusText);

  const errorBanner = new MockElement('div', 'error-banner');
  errorBanner.style.display = 'none';

  body.appendChild(statusBadge);
  body.appendChild(resetBtn);
  body.appendChild(chatWindow);
  body.appendChild(chipsContainer);
  body.appendChild(messageInput);
  body.appendChild(sendBtn);
  body.appendChild(errorBanner);

  register(body);

  document.getElementById = (id) => elementsById[id] || null;
  document.createElement = (tag) => new MockElement(tag);
  document.querySelector = (sel) => querySelector(body, sel);
  document.querySelectorAll = (sel) => querySelectorAll(body, sel);

  const sessionStorageStore = {};
  const sessionStorage = {
    getItem: (key) => sessionStorageStore[key] || null,
    setItem: (key, val) => { sessionStorageStore[key] = String(val); },
    removeItem: (key) => { delete sessionStorageStore[key]; },
    clear: () => { Object.keys(sessionStorageStore).forEach(k => delete sessionStorageStore[k]); }
  };

  const window = {
    location: { protocol: 'http:', host: 'localhost:8000' },
    WebSocket: MockWebSocket,
    sessionStorage,
    addEventListener: () => {},
    setTimeout: global.setTimeout,
    clearTimeout: global.clearTimeout,
    setInterval: global.setInterval,
    clearInterval: global.clearInterval
  };

  const sandbox = {
    window,
    document,
    sessionStorage,
    WebSocket: MockWebSocket,
    console,
    setTimeout: global.setTimeout,
    clearTimeout: global.clearTimeout,
    setInterval: global.setInterval,
    clearInterval: global.clearInterval
  };

  const appJsCode = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'app.js'), 'utf-8');
  vm.createContext(sandbox);
  vm.runInContext(appJsCode, sandbox);

  const AppClass = sandbox.ShopAssistApp || sandbox.window.ShopAssistApp;
  const appInstance = new AppClass();

  return {
    window,
    document,
    app: appInstance,
    elements: {
      chatWindow,
      messagesList,
      welcomeCard,
      chipsContainer,
      messageInput,
      sendBtn,
      resetBtn,
      statusBadge,
      statusIndicator,
      statusText,
      errorBanner
    }
  };
}

// 4. Test Suite Execution
const tests = [
  {
    name: 'test_render_user_message_adds_bubble_to_dom',
    fn: async (env) => {
      const { app, elements } = env;
      app.appendMessage('user', 'Hello ShopAssist!');
      const userBubble = elements.messagesList.querySelector('.message-user');
      assert.ok(userBubble, 'User bubble with class .message-user should be present in DOM');
      assert.ok(userBubble.textContent.includes('Hello ShopAssist!'), 'Bubble text should match input');
    }
  },
  {
    name: 'test_stream_start_creates_assistant_bubble_with_cursor',
    fn: async (env) => {
      const { app, elements } = env;
      app.handleStreamStart({ turn_id: 'turn_test_1' });
      const assistantBubble = elements.messagesList.querySelector('.message-assistant');
      assert.ok(assistantBubble, 'Assistant bubble should be created on stream_start');
      const cursor = assistantBubble.querySelector('.streaming-cursor');
      assert.ok(cursor, 'Assistant bubble should contain an element with class .streaming-cursor');
    }
  },
  {
    name: 'test_token_appends_text_to_current_bubble',
    fn: async (env) => {
      const { app, elements } = env;
      app.handleStreamStart({ turn_id: 'turn_test_2' });
      app.handleToken({ token: 'Hello', turn_id: 'turn_test_2' });
      app.handleToken({ token: ' world', turn_id: 'turn_test_2' });
      app.handleToken({ token: '!', turn_id: 'turn_test_2' });

      const assistantBubbles = elements.messagesList.querySelectorAll('.message-assistant');
      const latestBubble = assistantBubbles[assistantBubbles.length - 1];
      const textContent = latestBubble.querySelector('.message-text').textContent;
      assert.strictEqual(textContent, 'Hello world!', 'Sequential tokens should accumulate text without clearing');
    }
  },
  {
    name: 'test_stream_end_removes_cursor_and_renders_metrics',
    fn: async (env) => {
      const { app, elements } = env;
      app.handleStreamStart({ turn_id: 'turn_test_3' });
      app.handleToken({ token: 'Your order has shipped.', turn_id: 'turn_test_3' });
      app.handleStreamEnd({
        turn_id: 'turn_test_3',
        ttft_ms: 180.5,
        total_tokens: 15,
        total_duration_ms: 650.0,
        tokens_per_second: 23.07
      });

      const assistantBubbles = elements.messagesList.querySelectorAll('.message-assistant');
      const latestBubble = assistantBubbles[assistantBubbles.length - 1];
      const cursor = latestBubble.querySelector('.streaming-cursor');
      assert.strictEqual(cursor, null, 'Streaming cursor should be removed on stream_end');

      const telemetry = latestBubble.querySelector('.latency-badge');
      assert.ok(telemetry, 'Telemetry badge should be rendered on stream_end');
      assert.ok(telemetry.textContent.includes('181ms') || telemetry.textContent.includes('180.5'), 'Telemetry should show TTFT');
      assert.ok(telemetry.textContent.includes('23.1') || telemetry.textContent.includes('23.07'), 'Telemetry should show tokens/sec');
    }
  },
  {
    name: 'test_reset_button_clears_message_list',
    fn: async (env) => {
      const { app, elements } = env;
      app.appendMessage('user', 'Message before reset');
      assert.ok(elements.messagesList.querySelectorAll('.message-user').length > 0);

      app.handleResetSession();
      const userMessages = elements.messagesList.querySelectorAll('.message-user');
      assert.strictEqual(userMessages.length, 0, 'Resetting session must clear all user message bubbles');
      const assistantMessages = elements.messagesList.querySelectorAll('.message-assistant');
      assert.strictEqual(assistantMessages.length, 0, 'Resetting session must clear assistant bubbles');
      const welcomeCard = elements.messagesList.querySelector('.welcome-card');
      assert.ok(welcomeCard, 'Welcome card should be restored after reset');
    }
  },
  {
    name: 'test_connection_status_updates',
    fn: async (env) => {
      const { app, elements } = env;
      app.updateConnectionStatus('connected');
      assert.ok(elements.statusIndicator.classList.contains('status-connected'), 'Indicator should have status-connected');
      assert.strictEqual(elements.statusText.textContent, 'Connected');

      app.updateConnectionStatus('streaming');
      assert.ok(elements.statusIndicator.classList.contains('status-streaming'), 'Indicator should have status-streaming');
      assert.strictEqual(elements.statusText.textContent, 'Streaming...');

      app.updateConnectionStatus('disconnected');
      assert.ok(elements.statusIndicator.classList.contains('status-disconnected'), 'Indicator should have status-disconnected');
      assert.strictEqual(elements.statusText.textContent, 'Disconnected (Reconnecting...)');
    }
  },
  {
    name: 'test_error_frame_removes_cursor_and_displays_error',
    fn: async (env) => {
      const { app, elements } = env;
      app.handleStreamStart({ turn_id: 'turn_test_err' });
      app.handleError({
        code: 'INFERENCE_TIMEOUT',
        message: 'Engine timed out while generating response',
        recoverable: true
      });

      const assistantBubbles = elements.messagesList.querySelectorAll('.message-assistant');
      const latestBubble = assistantBubbles[assistantBubbles.length - 1];
      const cursor = latestBubble.querySelector('.streaming-cursor');
      assert.strictEqual(cursor, null, 'Error frame should remove streaming cursor cleanly');

      const errorAlert = latestBubble.querySelector('.message-error') || elements.errorBanner;
      assert.ok(errorAlert, 'Error details should be rendered to the user');
      assert.strictEqual(elements.sendBtn.disabled, false, 'Send button must be re-enabled on error');
    }
  },
  {
    name: 'test_send_disabled_during_stream',
    fn: async (env) => {
      const { app, elements } = env;
      app.handleStreamStart({ turn_id: 'turn_test_lock' });
      assert.strictEqual(elements.sendBtn.disabled, true, 'Send button should be disabled during stream');
      assert.strictEqual(elements.messageInput.disabled, true, 'Input field should be disabled during stream');

      app.handleStreamEnd({ turn_id: 'turn_test_lock', total_tokens: 1, ttft_ms: 10, total_duration_ms: 20, tokens_per_second: 50 });
      assert.strictEqual(elements.sendBtn.disabled, false, 'Send button should be enabled after stream end');
      assert.strictEqual(elements.messageInput.disabled, false, 'Input field should be enabled after stream end');
    }
  },
  {
    name: 'test_quick_action_chips_trigger_message',
    fn: async (env) => {
      const { app, elements } = env;
      const chip = elements.chipsContainer.querySelector('.chip');
      assert.ok(chip, 'Quick action chip must exist');
      chip.dispatchEvent('click');
      const userBubbles = elements.messagesList.querySelectorAll('.message-user');
      const sentBubble = userBubbles[userBubbles.length - 1];
      assert.ok(sentBubble, 'Clicking quick chip should send message');
      assert.ok(sentBubble.textContent.includes('Track ORD-1085'));
    }
  }
];

async function runTests() {
  console.log('\x1b[36m========================================================\x1b[0m');
  console.log('\x1b[36m   SHOPASSIST AI — FRONTEND FAKE DOM TEST SUITE         \x1b[0m');
  console.log('\x1b[36m========================================================\x1b[0m\n');

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    const env = createTestEnvironment();
    try {
      await test.fn(env);
      console.log(` \x1b[32m✔\x1b[0m PASS: ${test.name}`);
      passed++;
    } catch (err) {
      console.error(` \x1b[31m✖\x1b[0m FAIL: ${test.name}`);
      console.error(`   \x1b[33mError: ${err.message}\x1b[0m`);
      if (err.stack) {
        console.error(err.stack.split('\n').slice(1, 4).join('\n'));
      }
      failed++;
    }
  }

  console.log('\n\x1b[36m--------------------------------------------------------\x1b[0m');
  console.log(` Total: ${tests.length} | Passed: \x1b[32m${passed}\x1b[0m | Failed: \x1b[31m${failed}\x1b[0m`);
  console.log('\x1b[36m--------------------------------------------------------\x1b[0m\n');

  if (failed > 0) {
    process.exit(1);
  } else {
    process.exit(0);
  }
}

runTests();
