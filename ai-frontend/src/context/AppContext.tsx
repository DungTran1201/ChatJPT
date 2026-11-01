'use client';

import { createContext, useContext } from 'react';
import { Conversation } from '@/components/chat/Sidebar';
import { Language, getTranslation } from '@/utils/translations';

export type { Language };

export interface AppContextValue {
  currentUser: any;
  refreshUser: () => Promise<void>;
  conversations: Conversation[];
  activeConvId: string | null;
  setActiveConvId: (id: string | null) => void;
  fetchConversations: () => Promise<void>;
  createConversation: () => Promise<string | null>;
  renameConversation: (id: string, title: string) => Promise<void>;
  deleteConversation: (conv: Conversation) => Promise<void>;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (v: boolean) => void;
  handleLogout: () => Promise<void>;
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

export const AppContext = createContext<AppContextValue>({
  currentUser: null,
  refreshUser: async () => {},
  conversations: [],
  activeConvId: null,
  setActiveConvId: () => {},
  fetchConversations: async () => {},
  createConversation: async () => null,
  renameConversation: async () => {},
  deleteConversation: async () => {},
  sidebarCollapsed: false,
  setSidebarCollapsed: () => {},
  handleLogout: async () => {},
  language: 'vi',
  setLanguage: () => {},
  t: (key: string) => getTranslation('vi', key),
});

export function useApp() {
  return useContext(AppContext);
}
