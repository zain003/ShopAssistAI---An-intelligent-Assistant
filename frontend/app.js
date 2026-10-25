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
      this.micBtn = document.getElementById('mic-btn');
      this.voiceStatus = document.getElementById('voice-status');
      this.voiceStatusText = document.getElementById('voice-status-text');
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

      // Voice capture / playback
      this.isRecording = false;
      this.mediaStream = null;
      this.audioContext = null;
      this.scriptProcessor = null;
      this.ttsAudioContext = null;
      this.ttsQueue = [];
      this.ttsPlaying = false;
      this.pendingUserFromVoice = false;

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

        case 'asr_partial':
          if (payload && payload.text && this.voiceStatusText) {
            this.voiceStatusText.textContent = 'Hearing: ' + payload.text;
          }
          break;

        case 'asr_final':
          if (payload && payload.text) {
            this.appendMessage('user', payload.text);
            this.pendingUserFromVoice = true;
            if (this.voiceStatusText) {
              const ms = payload.asr_ms != null ? ` (${Math.round(payload.asr_ms)}ms ASR)` : '';
              this.voiceStatusText.textContent = 'Transcript ready' + ms;
            }
          }
          break;

        case 'tts_audio_chunk':
          if (payload && payload.audio_b64) {
            this.enqueueTtsAudio(payload.audio_b64, payload.format || 'wav');
          }
          break;

        case 'tts_end':
          // Playback continues from queue until empty
          break;

        case 'tool_call':
          this.renderToolBadge(
            'Calling tool: ' + (payload.tool || '?') +
            (payload.args ? ' ' + JSON.stringify(payload.args) : '')
          );
          break;

        case 'tool_result':
          this.renderToolBadge(
            'Tool result (' + (payload.tool || '?') + '): ' +
            JSON.stringify(payload.result || {}).slice(0, 180)
          );
          break;

        default:
          console.warn('Unknown envelope type received:', type);
          break;
      }
    }

    renderToolBadge(text) {
      if (!this.messagesList) return;
      const row = document.createElement('div');
      row.className = 'message-row message-assistant-row';
      const badge = document.createElement('div');
      badge.className = 'tool-call-badge';
      badge.textContent = text;
      row.appendChild(badge);
      this.messagesList.appendChild(row);
      this.scrollToBottom();
    }

    // ========================================================================
    // Voice capture (local mic → PCM16 chunks over WebSocket)
    // ========================================================================

    async toggleRecording() {
      if (this.isRecording) {
        await this.stopRecording(true);
      } else {
        await this.startRecording();
      }
    }

    async startRecording() {
      if (this.connectionState === 'streaming' || this.isRecording) return;
      if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
        this.showErrorBanner('Connect to the server before using voice.');
        return;
      }

      try {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
          },
        });
      } catch (err) {
        this.showErrorBanner('Microphone permission denied or unavailable.');
        return;
      }

      this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000,
      });
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      // ScriptProcessor is deprecated but widely available; buffer ~4096 samples
      const bufferSize = 4096;
      this.scriptProcessor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);
      this.scriptProcessor.onaudioprocess = (event) => {
        if (!this.isRecording) return;
        const input = event.inputBuffer.getChannelData(0);
        const pcm = this.floatTo16BitPCM(input);
        const b64 = this.arrayBufferToBase64(pcm.buffer);
        this.sendEnvelope('audio_chunk', {
          data: b64,
          sample_rate: this.audioContext.sampleRate || 16000,
          encoding: 'pcm_s16le',
        });
      };
      source.connect(this.scriptProcessor);
      this.scriptProcessor.connect(this.audioContext.destination);

      this.isRecording = true;
      if (this.micBtn) this.micBtn.classList.add('is-recording');
      if (this.voiceStatus) this.voiceStatus.style.display = 'flex';
      if (this.voiceStatusText) this.voiceStatusText.textContent = 'Listening... tap mic to send';
      this.setInputsDisabled(true);
      if (this.micBtn) this.micBtn.disabled = false;
    }

    async stopRecording(sendEnd) {
      this.isRecording = false;
      if (this.scriptProcessor) {
        try { this.scriptProcessor.disconnect(); } catch (e) {}
        this.scriptProcessor.onaudioprocess = null;
        this.scriptProcessor = null;
      }
      if (this.audioContext) {
        try { await this.audioContext.close(); } catch (e) {}
        this.audioContext = null;
      }
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach((t) => t.stop());
        this.mediaStream = null;
      }
      if (this.micBtn) this.micBtn.classList.remove('is-recording');
      if (sendEnd) {
        if (this.voiceStatusText) this.voiceStatusText.textContent = 'Transcribing...';
        this.sendEnvelope('audio_end', {});
      } else if (this.voiceStatus) {
        this.voiceStatus.style.display = 'none';
      }
      this.setInputsDisabled(false);
    }

    floatTo16BitPCM(float32Array) {
      const buffer = new ArrayBuffer(float32Array.length * 2);
      const view = new DataView(buffer);
      for (let i = 0; i < float32Array.length; i++) {
        let s = Math.max(-1, Math.min(1, float32Array[i]));
        view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
      }
      return new Int16Array(buffer);
    }

    arrayBufferToBase64(buffer) {
      const bytes = new Uint8Array(buffer);
      let binary = '';
      const chunk = 0x8000;
      for (let i = 0; i < bytes.length; i += chunk) {
        binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
      }
      return btoa(binary);
    }

    // ========================================================================
    // TTS playback queue
    // ========================================================================

    enqueueTtsAudio(audioB64, format) {
      this.ttsQueue.push({ audioB64: audioB64, format: format || 'wav' });
      if (!this.ttsPlaying) {
        this.playNextTts();
      }
    }

    async playNextTts() {
      if (!this.ttsQueue.length) {
        this.ttsPlaying = false;
        return;
      }
      this.ttsPlaying = true;
      const item = this.ttsQueue.shift();
      try {
        const binary = atob(item.audioB64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        if (!this.ttsAudioContext) {
          this.ttsAudioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        const audioBuffer = await this.ttsAudioContext.decodeAudioData(bytes.buffer.slice(0));
        const source = this.ttsAudioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.ttsAudioContext.destination);
        source.onended = () => this.playNextTts();
        source.start(0);
      } catch (err) {
        console.warn('TTS playback failed', err);
        this.playNextTts();
      }
    }

    // ========================================================================
    // Stream Accumulation & Rendering
    // ========================================================================

    handleStreamStart(payload) {
      this.updateConnectionStatus('streaming');
      this.setInputsDisabled(true);
      if (this.voiceStatus && this.pendingUserFromVoice) {
        if (this.voiceStatusText) this.voiceStatusText.textContent = 'Speaking reply...';
      }

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

        // Render visible source citations if present
        if (payload.citations && Array.isArray(payload.citations) && payload.citations.length > 0) {
          this.renderCitationBadges(this.activeStream.bubbleEl, payload.citations);
        } else if (payload.is_fallback || (payload.citations && Array.isArray(payload.citations) && payload.citations.length === 0)) {
          this.renderFallbackBadge(this.activeStream.bubbleEl);
        }

        // Render latency telemetry badge with retrieval metrics
        this.renderTelemetryBadge(this.activeStream.bubbleEl, payload);
        this.activeStream = null;
      }

      this.updateConnectionStatus('connected');
      this.setInputsDisabled(false);
      this.pendingUserFromVoice = false;
      if (this.voiceStatus) this.voiceStatus.style.display = 'none';
      this.scrollToBottom();
      if (this.messageInput) {
        this.messageInput.focus();
      }
    }

    renderCitationBadges(bubbleEl, citations) {
      if (!bubbleEl || !citations || citations.length === 0) return;

      const container = document.createElement('div');
      container.className = 'citations-container';

      const header = document.createElement('div');
      header.className = 'citations-header';
      header.textContent = 'Sources & Grounding:';
      container.appendChild(header);

      const list = document.createElement('div');
      list.className = 'citations-list';

      citations.forEach((citation) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'citation-item-wrapper';

        const pct = Math.round((citation.score || 0) * 100);
        const pill = document.createElement('button');
        pill.className = 'citation-pill';
        pill.type = 'button';
        pill.setAttribute('aria-expanded', 'false');
        pill.textContent = `📄 ${citation.title} (${pct}%)`;

        const drawer = document.createElement('div');
        drawer.className = 'citation-drawer';

        const drawerTitle = document.createElement('div');
        drawerTitle.className = 'citation-drawer-title';
        drawerTitle.textContent = `${citation.title} — ${citation.section_header}`;

        const snippet = document.createElement('div');
        snippet.className = 'citation-snippet';
        snippet.textContent = citation.snippet || '';

        drawer.appendChild(drawerTitle);
        drawer.appendChild(snippet);

        pill.addEventListener('click', () => {
          const isExpanded = drawer.classList.toggle('is-expanded');
          pill.classList.toggle('is-expanded', isExpanded);
          pill.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
        });

        wrapper.appendChild(pill);
        wrapper.appendChild(drawer);
        list.appendChild(wrapper);
      });

      container.appendChild(list);
      bubbleEl.appendChild(container);
    }

    renderFallbackBadge(bubbleEl) {
      if (!bubbleEl) return;
      const fallbackBadge = document.createElement('div');
      fallbackBadge.className = 'citation-fallback-badge';
      fallbackBadge.textContent = '💬 Direct Dialogue (No matching doc)';
      bubbleEl.appendChild(fallbackBadge);
    }

    renderTelemetryBadge(bubbleEl, payload) {
      if (!bubbleEl) return;

      const badge = document.createElement('div');
      badge.className = 'latency-badge';

      const appendMetric = (label, value) => {
        if (badge.childNodes.length > 0) {
          const dot = document.createElement('span');
          dot.textContent = ' • ';
          badge.appendChild(dot);
        }
        const span = document.createElement('span');
        span.className = 'latency-metric';
        span.textContent = `${label}: ${value}`;
        badge.appendChild(span);
      };

      if (payload.asr_ms != null) {
        appendMetric('ASR', Math.round(payload.asr_ms) + 'ms');
      }
      if (payload.retrieval_ms != null) {
        appendMetric('Retrieval', Math.round(payload.retrieval_ms) + 'ms');
      }
      if (payload.tool_ms != null) {
        appendMetric('Tools', Math.round(payload.tool_ms) + 'ms');
      }
      if (payload.tts_first_audio_ms != null) {
        appendMetric('TTS1st', Math.round(payload.tts_first_audio_ms) + 'ms');
      }
      if (payload.end_of_speech_to_first_audio_ms != null) {
        appendMetric('EoS→Audio', Math.round(payload.end_of_speech_to_first_audio_ms) + 'ms');
      }

      const ttft = payload.ttft_ms ? Math.round(payload.ttft_ms) : 0;
      const tokPerSec = payload.tokens_per_second != null ? Number(payload.tokens_per_second).toFixed(1) : '0';
      const totalTokens = payload.total_tokens || 0;

      appendMetric('TTFT', ttft + 'ms');
      appendMetric('Throughput', tokPerSec + ' tok/s');
      appendMetric('Tokens', String(totalTokens));

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
      if (this.isRecording) {
        this.stopRecording(false);
      }
      this.ttsQueue = [];
      this.clearMessagesDOM();
      this.clearSessionId();
      this.sendEnvelope('reset_session', {});
      this.updateConnectionStatus(this.socket && this.socket.readyState === WebSocket.OPEN ? 'connected' : 'disconnected');
      this.setInputsDisabled(false);
      if (this.voiceStatus) this.voiceStatus.style.display = 'none';
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

      // 4. Send envelope (enable_tts false for typed turns — optional)
      const sent = this.sendEnvelope('user_message', {
        text: text,
        enable_tts: false,
      });
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
      if (this.micBtn && !this.isRecording) this.micBtn.disabled = disabled;
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

      if (this.micBtn) {
        this.micBtn.addEventListener('click', (e) => {
          e.preventDefault();
          this.toggleRecording();
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
