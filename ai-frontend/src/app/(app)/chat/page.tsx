'use client';

import React, { useState, useEffect, useRef } from 'react';
import { AgentModel } from '@/types';
import { AttachmentService, AttachmentItem } from '@/services/attachmentService';
import { useApp } from '@/context/AppContext';
import ChatWorkspace, { Message } from '@/components/chat/ChatWorkspace';
import MessageComposer from '@/components/chat/MessageComposer';

export default function ChatPage() {
  const {
    currentUser,
    conversations,
    activeConvId,
    setActiveConvId,
    fetchConversations,
    createConversation,
    t,
  } = useApp();

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [showScrollBottom, setShowScrollBottom] = useState(false);

  const [activeModels, setActiveModels] = useState<AgentModel[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>('gemini-3.8-flash');
  const [selectedSenseiId, setSelectedSenseiId] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('ai_chan_selected_sensei') || 'sensei_sakura_n5';
    }
    return 'sensei_sakura_n5';
  });

  const handleSelectSensei = (senseiId: string) => {
    setSelectedSenseiId(senseiId);
    if (typeof window !== 'undefined') {
      localStorage.setItem('ai_chan_selected_sensei', senseiId);
    }
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatScrollContainerRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // ── Load models ───────────────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/v1/models?status=ACTIVE');
        if (!res.ok) return;
        const data: AgentModel[] = await res.json();
        setActiveModels(data);
        const def = data.find(m => m.is_default);
        setSelectedModelId((def ?? data[0])?.id ?? 'gemini-3.8-flash');
      } catch { /* fallback */ }
    })();
  }, []);

  // ── Load messages when activeConvId changes ───────────────────────
  useEffect(() => {
    if (!activeConvId) {
      setMessages([]);
      return;
    }
    let isCancelled = false;
    (async () => {
      try {
        const res = await fetch(`/api/v1/conversations/${activeConvId}/messages`);
        if (res.ok) {
          const data = await res.json();
          if (isCancelled) return;
          const loadedMsgs = (data.messages || []).map((m: any) => {
            const isRunning = m.status === 'RUNNING' || m.status === 'QUEUED';
            return {
              ...m,
              model: m.model_used || m.model,
              model_used: m.model_used || m.model,
              isStreaming: isRunning,
            };
          });
          setMessages(loadedMsgs);
        }
      } catch (err) {
        console.error('Failed to load messages:', err);
      }
    })();
    return () => {
      isCancelled = true;
    };
}, [activeConvId]);

// Clean up client subscription on unmount without cancelling backend turn
useEffect(() => {
  return () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };
}, []);

// ── Scroll ────────────────────────────────────────────────────────
const scrollToBottom = (smooth = true) => {
  messagesEndRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' });
};

useEffect(() => {
  if (!showScrollBottom) scrollToBottom();
}, [messages, isStreaming, showScrollBottom]);

const handleScroll = () => {
  if (!chatScrollContainerRef.current) return;
  const { scrollTop, scrollHeight, clientHeight } = chatScrollContainerRef.current;
  setShowScrollBottom(scrollHeight - scrollTop - clientHeight > 120);
};

const handleStopGeneration = async () => {
  if (abortControllerRef.current) {
    abortControllerRef.current.abort();
    abortControllerRef.current = null;
  }
  setIsStreaming(false);
};

// ── Send ──────────────────────────────────────────────────────────
const handleSendMessage = async (customPrompt?: string, attachmentIds?: string[]) => {
  const textToSend = customPrompt !== undefined ? customPrompt : inputPrompt;
  const hasAttachments = Boolean(attachmentIds && attachmentIds.length > 0);
  if ((!textToSend.trim() && !hasAttachments) || isStreaming) return;

  let targetConvId = activeConvId;

  if (!targetConvId) {
    targetConvId = await createConversation();
    if (!targetConvId) return;
  }

  let loadedAttachments: AttachmentItem[] = [];
  if (hasAttachments && attachmentIds) {
    try {
      const results = await Promise.all(
        attachmentIds.map(id => AttachmentService.getAttachment(id).catch(() => null))
      );
      loadedAttachments = results.filter(Boolean) as AttachmentItem[];
    } catch (err) {
      console.error('Failed to resolve attachment details:', err);
    }
  }

  const userMsg: Message = {
    id: `user-${Date.now()}`,
    role: 'user',
    content: textToSend.trim(),
    created_at: new Date().toISOString(),
    attachments: loadedAttachments.length > 0 ? loadedAttachments : undefined,
  };

  const assistantPlaceholderId = `assistant-${Date.now()}`;
  const assistantMsgPlaceholder: Message = {
    id: assistantPlaceholderId,
    role: 'assistant',
    content: '',
    model: selectedModelId,
    created_at: new Date().toISOString(),
    isStreaming: true,
  };

  setMessages(prev => [...prev, userMsg, assistantMsgPlaceholder]);
  setInputPrompt('');
  setIsStreaming(true);

  // ── Standard streaming ───────────────────────────────────────────
  const controller = new AbortController();
  abortControllerRef.current = controller;

  try {
    const response = await fetch(`/api/v1/conversations/${targetConvId}/messages/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: textToSend.trim(),
        model: selectedModelId,
        sensei_id: selectedSenseiId,
        attachments: attachmentIds && attachmentIds.length > 0 ? attachmentIds : undefined,
      }),
      signal: controller.signal,
    });

    if (!response.ok) {
      if (response.status === 429) {
        const errData = await response.json().catch(() => null);
        throw new Error(`🚨 ${errData?.detail?.message || 'Daily token quota exceeded.'}`);
      }
      throw new Error('Failed to connect to AI stream.');
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder('utf-8');
    let accumulatedText = '';

    if (reader) {
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.includes('event: chunk')) {
            const m = line.match(/data:\s*(.*)/);
            if (m) {
              try {
                const obj = JSON.parse(m[1]);
                if (obj.token) {
                  accumulatedText += obj.token;
                  setMessages(prev => prev.map(msg =>
                    msg.id === assistantPlaceholderId ? { ...msg, content: accumulatedText } : msg
                  ));
                }
              } catch { /* parse error */ }
            }
          } else if (line.includes('event: failover')) {
            const m = line.match(/data:\s*(.*)/);
            if (m) {
              try {
                const obj = JSON.parse(m[1]);
                const newModel = obj.to_model || 'offline-semantic-cache';
                const reason = obj.reason || obj.message || 'Mô hình tự động chuyển tiếp';
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantPlaceholderId
                    ? { ...msg, model: newModel, model_used: newModel, failoverNotice: reason }
                    : msg
                ));
                setSelectedModelId(newModel);
              } catch { /* parse error */ }
            }
          } else if (line.includes('event: done')) {
            const m = line.match(/data:\s*(.*)/);
            if (m) {
              try {
                const obj = JSON.parse(m[1]);
                if (obj.model) {
                  setMessages(prev => prev.map(msg =>
                    msg.id === assistantPlaceholderId
                      ? { ...msg, model: obj.model, model_used: obj.model }
                      : msg
                  ));
                }
              } catch { /* parse error */ }
            }
          } else if (line.includes('event: error')) {
            const m = line.match(/data:\s*(.*)/);
            if (m) {
              try {
                const obj = JSON.parse(m[1]);
                accumulatedText = `⚠️ **Error:** ${obj.message || 'Unknown error'}`;
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantPlaceholderId ? { ...msg, content: accumulatedText } : msg
                ));
              } catch { /* parse error */ }
            }
          }
        }
      }
    }
  } catch (err: any) {
    if (err.name !== 'AbortError') {
      setMessages(prev => prev.map(m =>
        m.id === assistantPlaceholderId
          ? { ...m, content: m.content || `⚠️ Connection error: ${err.message}` }
          : m
      ));
    }
  } finally {
    setIsStreaming(false);
    abortControllerRef.current = null;
    setMessages(prev => prev.map(m =>
      m.id === assistantPlaceholderId
        ? { ...m, isStreaming: false, content: m.content || 'No response received.' }
        : m
    ));
    fetchConversations();
  }
};

const activeConv = conversations.find(c => c.id === activeConvId);

return (
  <>
    <ChatWorkspace
      messages={messages}
      isStreaming={isStreaming}
      onSelectPrompt={p => {
        setInputPrompt(p);
        handleSendMessage(p);
      }}
      onStop={handleStopGeneration}
      activeConvTitle={activeConv?.title}
      currentUser={currentUser}
      chatScrollContainerRef={chatScrollContainerRef}
      messagesEndRef={messagesEndRef}
      onScroll={handleScroll}
      showScrollBottom={showScrollBottom}
      scrollToBottom={() => scrollToBottom(true)}
    />
    <div style={{ padding: '0 1.5rem', flexShrink: 0 }}>
      <MessageComposer
        inputPrompt={inputPrompt}
        onInputChange={setInputPrompt}
        onSend={handleSendMessage}
        onStop={handleStopGeneration}
        isStreaming={isStreaming}
        activeModels={activeModels}
        selectedModelId={selectedModelId}
        onSelectModel={setSelectedModelId}
        selectedSenseiId={selectedSenseiId}
        onSelectSensei={handleSelectSensei}
        placeholder={t("chat.composer_placeholder")}
      />
    </div>
  </>
);
}
