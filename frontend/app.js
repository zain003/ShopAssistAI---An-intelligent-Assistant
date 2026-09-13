/**
 * ShopAssist AI — Frontend Application & WebSocket Stream Renderer
 * 
 * Implements bidirectional WebSocket protocol per FEAT-003-BE and FEAT-004-FE,
 * word-by-word token accumulation, blinking cursor animation, session resets,
 * quick action chips, and latency telemetry badges.
 */

(function (global) {
  'use strict';

  class ShopAssistApp {
    constructor() {
      // DOM Elements
      this.chatWindow = document.getElementById('chat-window');
      this.messagesList = document.getElementById('messages-list');
      this.welcomeCard = document.getElementById('welcome-card');
      this.chipsContainer = document.getElementById('chips-container');
      this.messageInput = document.getElementById('message-input');
      this.sendBtn = document.getElementById('send-btn');
      this.resetBtn = document.getElementById('reset-btn');
      this.statusBadge = document.getElementById('status-badge');
      this.statusIndicator = document.getElementById('status-indicator');
      this.statusText = document.getElementById('status-text');
      this.errorBanner = document.getElementById('error-banner');
      this.errorText = document.getElementById('error-text');
      this.errorDismissBtn = document.getElementById('error-dismiss-btn');

      // State
      this.sessionId = this.loadSessionId();
      this.socket = null;
      this.connectionState = 'disconnected'; // 'connecting' | 'connected' | 'streaming' | 'disconnected'
      this.reconnectAttempts = 0;
      this.maxReconnectDelayMs = 10000;
      this.reconnectTimer = null;
      this.heartbeatTimer = null;
      this.activeStream = null; // { turnId, bubbleEl, textEl, cursorEl, text: "" }

      // Initialization
      this.initEvents();
      this.connectWebSocket();
    }

    // ========================================================================
    // Session Storage
    // ========================================================================

    loadSessionId() {
      try {
        if (typeof sessionStorage !== 'undefined') {
          return sessionStorage.getItem('shopassist_session_id') || null;
        }
      } catch (e) {
        // Fallback for restricted storage environments
      }
      return null;
    }

    saveSessionId(id) {
      this.sessionId = id;
      try {
        if (typeof sessionStorage !== 'undefined') {
          sessionStorage.setItem('shopassist_session_id', id);
        }
      } catch (e) {}
    }

    clearSessionId() {
      this.sessionId = null;
      try {
        if (typeof sessionStorage !== 'undefined') {
          sessionStorage.removeItem('shopassist_session_id');
        }
      } catch (e) {}
    }

    // ========================================================================
    // WebSocket Connection Lifecycle
    // ========================================================================

    getWebSocketUrl() {
      let protocol = 'ws:';
      let host = 'localhost:8000';
      if (typeof window !== 'undefined' && window.location) {
        protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        host = window.location.host || 'localhost:8000';
      }
      let url = `${protocol}//${host}/ws/chat`;
      if (this.sessionId) {
        url += `?session_id=${encodeURIComponent(this.sessionId)}`;
      }
      return url;
    }

    connectWebSocket() {
      if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
        return;
      }

      this.updateConnectionStatus('connecting');

      try {
        const wsUrl = this.getWebSocketUrl();
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
          this.reconnectAttempts = 0;
          this.updateConnectionStatus('connected');
          this.hideErrorBanner();
          this.startHeartbeat();
        };

        this.socket.onmessage = (event) => {
          this.handleIncomingMessage(event.data);
        };

        this.socket.onclose = (event) => {
          this.stopHeartbeat();
          this.updateConnectionStatus('disconnected');
          if (this.activeStream) {
            this.handleError({
              code: 'SOCKET_CLOSED',
              message: 'Connection closed unexpectedly during response',
              recoverable: true
            });
          }
          this.scheduleReconnect();
        };

        this.socket.onerror = (err) => {
          this.updateConnectionStatus('disconnected');
        };
      } catch (err) {
        this.updateConnectionStatus('disconnected');
        this.scheduleReconnect();
      }
    }

    scheduleReconnect() {
      if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
      const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), this.maxReconnectDelayMs);
      this.reconnectAttempts++;
      this.reconnectTimer = setTimeout(() => {
        this.connectWebSocket();
      }, delay);
    }

    startHeartbeat() {
      this.stopHeartbeat();
      this.heartbeatTimer = setInterval(() => {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.sendEnvelope('ping');
        }
      }, 30000);
    }

    stopHeartbeat() {
      if (this.heartbeatTimer) {
        clearInterval(this.heartbeatTimer);
        this.heartbeatTimer = null;
      }
    }

    sendEnvelope(type, payload = {}) {
      if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
        this.showErrorBanner('Not connected to assistant server. Reconnecting...');
        return false;
      }

      const envelope = {
        type: type,
        session_id: this.sessionId,
        payload: payload
      };

      try {
        this.socket.send(JSON.stringify(envelope));
        return true;
      } catch (err) {
        this.showErrorBanner('Failed to send message over socket.');
        return false;
      }
    }

    // ========================================================================
    // Message Router (Protocol Envelopes)
    // ========================================================================

    handleIncomingMessage(raw) {
      let data;
      try {
        data = typeof raw === 'string' ? JSON.parse(raw) : raw;
      } catch (e) {
        console.error('Failed to parse incoming WebSocket JSON:', raw);
        return;
      }

      const { type, session_id, payload } = data;

      if (session_id && session_id !== this.sessionId) {
        this.saveSessionId(session_id);
      }

      switch (type) {
        case 'session_created':
          if (payload && payload.session_id) {
            this.saveSessionId(payload.session_id);
          }
          break;

        case 'session_reset':
          this.finalizeResetSession();
          break;

        case 'stream_start':
          this.handleStreamStart(payload || {});
          break;

        case 'token':
          this.handleToken(payload || {});
          break;

        case 'stream_end':
          this.handleStreamEnd(payload || {});
          break;

        case 'error':
          this.handleError(payload || {});
          break;

        case 'pong':
          // Heartbeat acknowledged
          break;

        default:
          console.warn('Unknown envelope type received:', type);
          break;
      }
    }

    // ========================================================================
    // Stream Accumulation & Rendering
    // ========================================================================

    handleStreamStart(payload) {
      this.updateConnectionStatus('streaming');
      this.setInputsDisabled(true);

      const turnId = payload.turn_id || `turn_${Date.now()}`;

      // Create assistant message bubble
      const row = document.createElement('div');
      row.className = 'message-row message-assistant-row';

      const bubble = document.createElement('div');
      bubble.className = 'message-bubble message-assistant';

      const textEl = document.createElement('span');
      textEl.className = 'message-text';

      const cursor = document.createElement('span');
      cursor.className = 'streaming-cursor';

      bubble.appendChild(textEl);
      bubble.appendChild(cursor);
      row.appendChild(bubble);

      if (this.messagesList) {
        this.messagesList.appendChild(row);
      }

      this.activeStream = {
        turnId: turnId,
        rowEl: row,
        bubbleEl: bubble,
        textEl: textEl,
        cursorEl: cursor,
        text: ''
      };

      this.scrollToBottom();
    }

    handleToken(payload) {
      const token = payload.token || '';
      if (!this.activeStream) {
        // Recover if token arrives without stream_start
        this.handleStreamStart({ turn_id: payload.turn_id });
      }

      this.activeStream.text += token;
      this.activeStream.textEl.textContent = this.activeStream.text;
      this.scrollToBottom();
    }

    handleStreamEnd(payload) {
      if (this.activeStream) {
        // Remove streaming cursor
        if (this.activeStream.cursorEl && this.activeStream.cursorEl.parentNode) {
          this.activeStream.cursorEl.parentNode.removeChild(this.activeStream.cursorEl);
        }

        // Render latency telemetry badge
        this.renderTelemetryBadge(this.activeStream.bubbleEl, payload);
        this.activeStream = null;
      }

      this.updateConnectionStatus('connected');
      this.setInputsDisabled(false);
      this.scrollToBottom();
      if (this.messageInput) {
        this.messageInput.focus();
      }
    }

    renderTelemetryBadge(bubbleEl, payload) {
      if (!bubbleEl) return;

      const badge = document.createElement('div');
      badge.className = 'latency-badge';

      const ttft = payload.ttft_ms ? Math.round(payload.ttft_ms) : 0;
      const tokPerSec = payload.tokens_per_second != null ? Number(payload.tokens_per_second).toFixed(1) : '0';
      const totalTokens = payload.total_tokens || 0;

      const ttftSpan = document.createElement('span');
      ttftSpan.className = 'latency-metric';
      ttftSpan.textContent = `TTFT: ${ttft}ms`;

      const dot1 = document.createElement('span');
      dot1.textContent = ' • ';

      const tpsSpan = document.createElement('span');
      tpsSpan.className = 'latency-metric';
      tpsSpan.textContent = `${tokPerSec} tok/s`;

      const dot2 = document.createElement('span');
      dot2.textContent = ' • ';

      const tokSpan = document.createElement('span');
      tokSpan.className = 'latency-metric';
      tokSpan.textContent = `${totalTokens} tokens`;

      badge.appendChild(ttftSpan);
      badge.appendChild(dot1);
      badge.appendChild(tpsSpan);
      badge.appendChild(dot2);
      badge.appendChild(tokSpan);

      bubbleEl.appendChild(badge);
    }

    handleError(payload) {
      if (this.activeStream) {
        // Remove cursor
        if (this.activeStream.cursorEl && this.activeStream.cursorEl.parentNode) {
          this.activeStream.cursorEl.parentNode.removeChild(this.activeStream.cursorEl);
        }

        // Render inline error badge inside assistant bubble
        const errDiv = document.createElement('div');
        errDiv.className = 'message-error';
        const msg = payload.message || 'An error occurred during response generation';
        const code = payload.code ? `[${payload.code}] ` : '';
        errDiv.textContent = `${code}${msg}`;
        this.activeStream.bubbleEl.appendChild(errDiv);

        this.activeStream = null;
      } else {
        // Standalone error banner
        this.showErrorBanner(payload.message || 'An unexpected error occurred');
      }

      this.updateConnectionStatus(this.socket && this.socket.readyState === WebSocket.OPEN ? 'connected' : 'disconnected');
      this.setInputsDisabled(false);
      this.scrollToBottom();
    }

    // ========================================================================
    // DOM Message Append & Reset
    // ========================================================================

    appendMessage(role, text) {
      if (!this.messagesList) return null;

      // Hide welcome card upon first user interaction
      if (this.welcomeCard) {
        this.welcomeCard.style.display = 'none';
      }

      const row = document.createElement('div');
      row.className = `message-row message-${role}-row`;

      const bubble = document.createElement('div');
      bubble.className = `message-bubble message-${role}`;

      const textEl = document.createElement('span');
      textEl.className = 'message-text';
      textEl.textContent = text;

      bubble.appendChild(textEl);
      row.appendChild(bubble);
      this.messagesList.appendChild(row);

      this.scrollToBottom();
      return bubble;
    }

    handleResetSession() {
      // Clear DOM messages
      this.clearMessagesDOM();

      // Reset local session ID
      this.clearSessionId();

      // Emit reset_session frame to server if connected
      this.sendEnvelope('reset_session', {});

      this.updateConnectionStatus(this.socket && this.socket.readyState === WebSocket.OPEN ? 'connected' : 'disconnected');
      this.setInputsDisabled(false);
      if (this.messageInput) {
        this.messageInput.value = '';
        this.messageInput.focus();
      }
    }

    finalizeResetSession() {
      this.clearMessagesDOM();
    }

    clearMessagesDOM() {
      if (!this.messagesList) return;

      // Remove all user and assistant rows
      const rows = this.messagesList.querySelectorAll('.message-row');
      for (const row of rows) {
        if (row.parentNode) row.parentNode.removeChild(row);
      }

      // Restore welcome card
      if (this.welcomeCard) {
        this.welcomeCard.style.display = 'block';
        if (!this.welcomeCard.parentNode) {
          this.messagesList.appendChild(this.welcomeCard);
        }
      }
    }

    // ========================================================================
    // User Action Handlers
    // ========================================================================

    sendMessage(rawText) {
      if (!rawText) return;
      const text = rawText.trim();
      if (!text) return;

      if (this.connectionState === 'streaming') {
        return; // Prevent submissions during active streaming
      }

      // 1. Immediately append user bubble to DOM (AC-1)
      this.appendMessage('user', text);

      // 2. Clear input
      if (this.messageInput) {
        this.messageInput.value = '';
        this.adjustTextareaHeight();
      }

      // 3. Ensure socket is connected
      if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
        this.connectWebSocket();
      }

      // 4. Send envelope
      const sent = this.sendEnvelope('user_message', { text: text });
      if (!sent) {
        this.handleError({
          code: 'SEND_FAILED',
          message: 'Unable to deliver message. Check connection.',
          recoverable: true
        });
      }
    }

    // ========================================================================
    // UI Helpers & State Updates
    // ========================================================================

    updateConnectionStatus(state) {
      this.connectionState = state;

      if (!this.statusIndicator || !this.statusText) return;

      this.statusIndicator.classList.remove('status-connecting', 'status-connected', 'status-streaming', 'status-disconnected');

      switch (state) {
        case 'connected':
          this.statusIndicator.classList.add('status-connected');
          this.statusText.textContent = 'Connected';
          break;
        case 'streaming':
          this.statusIndicator.classList.add('status-streaming');
          this.statusText.textContent = 'Streaming...';
          break;
        case 'connecting':
          this.statusIndicator.classList.add('status-connecting');
          this.statusText.textContent = 'Connecting...';
          break;
        case 'disconnected':
        default:
          this.statusIndicator.classList.add('status-disconnected');
          this.statusText.textContent = 'Disconnected (Reconnecting...)';
          break;
      }
    }

    setInputsDisabled(disabled) {
      if (this.sendBtn) this.sendBtn.disabled = disabled;
      if (this.messageInput) this.messageInput.disabled = disabled;
      if (this.chipsContainer) {
        const chips = this.chipsContainer.querySelectorAll('.chip');
        for (const chip of chips) {
          chip.disabled = disabled;
        }
      }
    }

    scrollToBottom() {
      if (!this.chatWindow) return;
      this.chatWindow.scrollTop = this.chatWindow.scrollHeight;
    }

    adjustTextareaHeight() {
      if (!this.messageInput) return;
      this.messageInput.style.height = 'auto';
      const scrollHeight = this.messageInput.scrollHeight;
      this.messageInput.style.height = Math.min(scrollHeight, 140) + 'px';
    }

    showErrorBanner(msg) {
      if (!this.errorBanner) return;
      if (this.errorText) this.errorText.textContent = msg;
      this.errorBanner.style.display = 'flex';
    }

    hideErrorBanner() {
      if (this.errorBanner) {
        this.errorBanner.style.display = 'none';
      }
    }

    // ========================================================================
    // Event Listeners Binding
    // ========================================================================

    initEvents() {
      // Send button click
      if (this.sendBtn) {
        this.sendBtn.addEventListener('click', (e) => {
          e.preventDefault();
          if (this.messageInput) {
            this.sendMessage(this.messageInput.value);
          }
        });
      }

      // Enter key submits, Shift+Enter new line
      if (this.messageInput) {
        this.messageInput.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage(this.messageInput.value);
          }
        });

        this.messageInput.addEventListener('input', () => {
          this.adjustTextareaHeight();
        });
      }

      // Quick action chips
      if (this.chipsContainer) {
        this.chipsContainer.addEventListener('click', (e) => {
          let target = e.target;
          while (target && target !== this.chipsContainer) {
            if (target.classList && target.classList.contains('chip')) {
              const prompt = target.getAttribute('data-prompt') || target.textContent;
              this.sendMessage(prompt);
              break;
            }
            target = target.parentNode;
          }
        });
      }

      // Reset button click
      if (this.resetBtn) {
        this.resetBtn.addEventListener('click', (e) => {
          e.preventDefault();
          this.handleResetSession();
        });
      }

      // Error banner dismiss
      if (this.errorDismissBtn) {
        this.errorDismissBtn.addEventListener('click', () => {
          this.hideErrorBanner();
        });
      }
    }
  }

  // Export or attach to global window
  if (typeof window !== 'undefined') {
    window.ShopAssistApp = ShopAssistApp;
    window.addEventListener('DOMContentLoaded', () => {
      window.shopAssistInstance = new ShopAssistApp();
    });
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ShopAssistApp };
  }
})(typeof window !== 'undefined' ? window : global);
