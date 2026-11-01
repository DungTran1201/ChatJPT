'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import DesktopHeader from '@/components/chat/DesktopHeader';
import Sidebar, { Conversation } from '@/components/chat/Sidebar';
import { AppContext, AppContextValue } from '@/context/AppContext';

// ── Shell ──────────────────────────────────────────────────────────────
export default function AppShellLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  const [currentUser, setCurrentUser] = useState<any>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);

  // ── Auth check ───────────────────────────────────────────────────────
  const fetchCurrentUser = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/auth/me');
      if (!res.ok) { router.push('/login'); return; }
      const data = await res.json();
      setCurrentUser(data.user);
      setAuthChecked(true);
    } catch {
      router.push('/login');
    }
  }, [router]);

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  // Synchronize dynamic personal preferences to root styles
  useEffect(() => {
    if (typeof document === 'undefined') return;
    const root = document.documentElement;
    if (!currentUser) return;

    const customBg = currentUser.custom_bg_url;
    const opacityVal = currentUser.bg_opacity !== undefined && currentUser.bg_opacity !== null ? currentUser.bg_opacity : 90;
    const blurVal = currentUser.bg_blur !== undefined && currentUser.bg_blur !== null ? currentUser.bg_blur : 12;
    const accent = currentUser.accent_color || 'emerald';
    const fontSize = currentUser.ui_font_size || 'medium';

    const accentPalette: Record<string, { accent: string; hover: string; border: string; glow: string; subtle: string }> = {
      emerald: { accent: '#3ecf8e', hover: '#5ad9a0', border: 'rgba(62, 207, 142, 0.30)', glow: '0 0 16px rgba(62, 207, 142, 0.18)', subtle: 'rgba(62, 207, 142, 0.10)' },
      sakura:  { accent: '#ec4899', hover: '#f472b6', border: 'rgba(236, 72, 153, 0.30)', glow: '0 0 16px rgba(236, 72, 153, 0.18)', subtle: 'rgba(236, 72, 153, 0.10)' },
      violet:  { accent: '#8b5cf6', hover: '#a78bfa', border: 'rgba(139, 92, 246, 0.30)', glow: '0 0 16px rgba(139, 92, 246, 0.18)', subtle: 'rgba(139, 92, 246, 0.10)' },
      amber:   { accent: '#f59e0b', hover: '#fbbf24', border: 'rgba(245, 158, 11, 0.30)', glow: '0 0 16px rgba(245, 158, 11, 0.18)', subtle: 'rgba(245, 158, 11, 0.10)' },
      sky:     { accent: '#0ea5e9', hover: '#38bdf8', border: 'rgba(14, 165, 233, 0.30)', glow: '0 0 16px rgba(14, 165, 233, 0.18)', subtle: 'rgba(14, 165, 233, 0.10)' },
    };
    const activePalette = accentPalette[accent] || accentPalette.emerald;

    if (customBg) {
      const alpha = opacityVal / 100;
      root.style.setProperty('--bg-base', `rgba(15, 15, 16, ${alpha})`);
      root.style.setProperty('--bg-surface', `rgba(21, 21, 22, ${Math.min(1, alpha + 0.05)})`);
      root.style.setProperty('--bg-elevated', `rgba(28, 28, 31, ${Math.min(1, alpha + 0.10)})`);
      root.style.setProperty('--bg-overlay', `rgba(34, 34, 37, ${Math.min(1, alpha + 0.15)})`);
      root.style.setProperty('--app-backdrop-blur', `${blurVal}px`);
    } else {
      root.style.removeProperty('--bg-base');
      root.style.removeProperty('--bg-surface');
      root.style.removeProperty('--bg-elevated');
      root.style.removeProperty('--bg-overlay');
      root.style.removeProperty('--app-backdrop-blur');
    }

    // Set dynamic accent theme
    root.style.setProperty('--accent', activePalette.accent);
    root.style.setProperty('--accent-hover', activePalette.hover);
    root.style.setProperty('--accent-border', activePalette.border);
    root.style.setProperty('--accent-glow', activePalette.glow);
    root.style.setProperty('--accent-subtle', activePalette.subtle);
    root.style.setProperty('--primary', activePalette.accent);
    root.style.setProperty('--primary-hover', activePalette.hover);

    // Font size scaling
    if (fontSize === 'small') {
      root.style.setProperty('--font-size-base', '13px');
      root.style.fontSize = '14px';
    } else if (fontSize === 'large') {
      root.style.setProperty('--font-size-base', '15px');
      root.style.fontSize = '17px';
    } else {
      root.style.removeProperty('--font-size-base');
      root.style.fontSize = '16px';
    }
  }, [currentUser]);


  // ── Conversations ────────────────────────────────────────────────────
  const fetchConversations = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/conversations/');
      if (res.ok) {
        const data = await res.json();
        setConversations(data.conversations || []);
      } else if (res.status === 401) {
        router.push('/login');
      }
    } catch { /* ignored */ }
  }, [router]);

  useEffect(() => {
    if (authChecked) fetchConversations();
  }, [authChecked, fetchConversations]);

  const createConversation = useCallback(async (): Promise<string | null> => {
    try {
      const res = await fetch('/api/v1/conversations/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Conversation' }),
      });
      if (res.ok) {
        const data = await res.json();
        const newConv = data.conversation;
        setConversations(prev => [newConv, ...prev]);
        setActiveConvId(newConv.id);
        return newConv.id;
      }
    } catch (err) {
      console.error('Failed to create conversation:', err);
    }
    return null;
  }, []);

  const renameConversation = useCallback(async (convId: string, newTitle: string) => {
    try {
      const res = await fetch(`/api/v1/conversations/${convId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle }),
      });
      if (res.ok) {
        setConversations(prev => prev.map(c => c.id === convId ? { ...c, title: newTitle } : c));
      }
    } catch (err) {
      console.error('Failed to rename:', err);
    }
  }, []);

  const deleteConversation = useCallback(async (conv: Conversation) => {
    if (!confirm(`Delete conversation "${conv.title}"?`)) return;
    try {
      const res = await fetch(`/api/v1/conversations/${conv.id}`, { method: 'DELETE' });
      if (res.status === 204 || res.ok) {
        setConversations(prev => prev.filter(c => c.id !== conv.id));
        if (activeConvId === conv.id) setActiveConvId(null);
      }
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  }, [activeConvId]);

  const handleLogout = useCallback(async () => {
    try {
      await fetch('/api/v1/auth/logout', { method: 'POST' });
      localStorage.removeItem('ai_chan_user');
      localStorage.removeItem('ai_chan_token');
    } finally {
      router.push('/login');
    }
  }, [router]);

  // Handle new chat from sidebar
  const handleNewChat = useCallback(async () => {
    const id = await createConversation();
    if (id) {
      setActiveConvId(id);
      router.push('/chat');
    }
  }, [createConversation, router]);

  // Handle selecting a conversation
  const handleSelectConversation = useCallback((convId: string) => {
    setActiveConvId(convId);
    if (pathname !== '/chat') router.push('/chat');
  }, [pathname, router]);

  if (!authChecked) {
    return (
      <div style={{
        height: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center',
        backgroundColor: 'var(--bg-base)', color: 'var(--text-muted)', fontSize: '0.85rem',
      }}>
        Loading…
      </div>
    );
  }

  const ctx: AppContextValue = {
    currentUser,
    refreshUser: fetchCurrentUser,
    conversations,
    activeConvId,
    setActiveConvId,
    fetchConversations,
    createConversation,
    renameConversation,
    deleteConversation,
    sidebarCollapsed,
    setSidebarCollapsed,
    handleLogout,
  };

  const customBg = currentUser?.custom_bg_url;
  const blurVal = currentUser?.bg_blur !== undefined && currentUser?.bg_blur !== null ? currentUser.bg_blur : 12;

  return (
    <AppContext.Provider value={ctx}>
      {customBg && (
        <div
          data-testid="app-custom-background"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundImage: `url("${customBg}")`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
            zIndex: 0,
            pointerEvents: 'none',
          }}
        />
      )}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '100dvh',
          overflow: 'hidden',
          backgroundColor: customBg ? 'transparent' : 'var(--bg-base)',
          position: 'relative',
          zIndex: 1,
          backdropFilter: customBg ? `blur(${blurVal}px)` : undefined,
          WebkitBackdropFilter: customBg ? `blur(${blurVal}px)` : undefined,
        }}
      >
        {/* Global header */}
        <DesktopHeader
          currentUser={currentUser}
          onLogout={handleLogout}
        />

        {/* Body: sidebar + main */}
        <div
          style={{
          display: 'flex',
          flex: 1,
          overflow: 'hidden',
          minHeight: 0,
        }}
      >
          <Sidebar
            conversations={conversations}
            activeConvId={activeConvId}
            onSelectConversation={handleSelectConversation}
            onNewChat={handleNewChat}
            onRenameConversation={renameConversation}
            onDeleteConversation={deleteConversation}
            collapsed={sidebarCollapsed}
            onToggleCollapse={() => setSidebarCollapsed(v => !v)}
          />

          <main
            style={{
              flex: 1,
              minWidth: 0,
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
            }}
          >
            {children}
          </main>
        </div>
      </div>
    </AppContext.Provider>
  );
}
