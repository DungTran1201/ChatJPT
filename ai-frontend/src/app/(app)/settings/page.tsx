'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { AgentModel, ModelSearchResponse } from '@/types';
import Icon from '@/components/ui/Icon';
import { useApp } from '@/context/AppContext';
import ApiKeysTab from '@/components/settings/ApiKeysTab';

interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  username: string;
  avatar_url: string;
  bio: string;
  phone_number: string;
  age?: number | null;
  occupation?: string;
  interests?: string;
  japanese_level?: string;
  learning_goal?: string;
  custom_bg_url?: string;
  bg_opacity?: number;
  bg_blur?: number;
  accent_color?: string;
  ui_font_size?: 'small' | 'medium' | 'large';
  theme_preference: 'DARK' | 'LIGHT' | 'SYSTEM';
  language_preference: 'vi' | 'en';
  status: string;
  created_at: string;
  last_login_at?: string;
  discord_id?: string;
  discord_username?: string;
}

interface UserStats {
  total_conversations: number;
  total_messages: number;
}

export default function SettingsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshUser } = useApp();

  // Active tab state: 'profile' | 'security' | 'preferences' | 'models' | 'api-keys'
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'preferences' | 'models' | 'api-keys'>('profile');

  // Sync tab from URL ?tab= param
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab && ['profile', 'security', 'preferences', 'models', 'api-keys'].includes(tab)) {
      setActiveTab(tab as any);
    }
  }, [searchParams]);

  // User data
  const [user, setUser] = useState<UserProfile | null>(null);
  const [stats, setStats] = useState<UserStats>({ total_conversations: 0, total_messages: 0 });
  const [loadingInitial, setLoadingInitial] = useState(true);



  // Notifications
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Tab 1: Profile form state
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [bio, setBio] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [age, setAge] = useState('');
  const [occupation, setOccupation] = useState('');
  const [interests, setInterests] = useState('');
  const [japaneseLevel, setJapaneseLevel] = useState('CHUA_HOC');
  const [learningGoal, setLearningGoal] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [showAvatarEdit, setShowAvatarEdit] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);

  // Tab 2: Security form state
  // Change Email
  const [newEmail, setNewEmail] = useState('');
  const [emailCurrentPassword, setEmailCurrentPassword] = useState('');
  const [savingEmail, setSavingEmail] = useState(false);

  // Change Password
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [savingPassword, setSavingPassword] = useState(false);

  // Tab 3: Preferences state
  const [themePreference, setThemePreference] = useState<'DARK' | 'LIGHT' | 'SYSTEM'>('DARK');
  const [languagePreference, setLanguagePreference] = useState<'vi' | 'en'>('vi');
  const [customBgUrl, setCustomBgUrl] = useState('');
  const [bgOpacity, setBgOpacity] = useState<number>(90);
  const [bgBlur, setBgBlur] = useState<number>(12);
  const [accentColor, setAccentColor] = useState<string>('emerald');
  const [uiFontSize, setUiFontSize] = useState<'small' | 'medium' | 'large'>('medium');
  const [savingPreferences, setSavingPreferences] = useState(false);

  const WALLPAPER_PRESETS = [
    { id: 'none', label: 'Mặc định (Không nền)', url: '' },
    { id: 'sakura', label: 'Vườn Sakura', url: 'https://images.unsplash.com/photo-1522383225653-ed111181a951?auto=format&fit=crop&w=1920&q=80' },
    { id: 'fuji', label: 'Núi Phú Sĩ', url: 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=1920&q=80' },
    { id: 'tokyo', label: 'Đêm Tokyo', url: 'https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=1920&q=80' },
    { id: 'kyoto', label: 'Rừng Trúc Kyoto', url: 'https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=1920&q=80' },
    { id: 'cyberpunk', label: 'Cyberpunk Shinjuku', url: 'https://images.unsplash.com/photo-1542051841857-5f90071e7989?auto=format&fit=crop&w=1920&q=80' },
  ];

  const ACCENT_PRESETS = [
    { id: 'emerald', name: 'Emerald', hex: '#3ecf8e', desc: 'Mặc định sắc nét' },
    { id: 'sakura', name: 'Sakura', hex: '#ec4899', desc: 'Hồng hoa anh đào' },
    { id: 'violet', name: 'Violet', hex: '#8b5cf6', desc: 'Tím mộng mơ' },
    { id: 'amber', name: 'Amber', hex: '#f59e0b', desc: 'Hổ phách ấm' },
    { id: 'sky', name: 'Sky Blue', hex: '#0ea5e9', desc: 'Lam thanh thoát' },
  ];

  const FONT_SIZE_PRESETS = [
    { id: 'small', label: 'Nhỏ (13px)', desc: 'Mật độ cao, hiển thị nhiều nội dung hơn' },
    { id: 'medium', label: 'Tiêu chuẩn (14px)', desc: 'Cân bằng chuẩn' },
    { id: 'large', label: 'Lớn (15px)', desc: 'Dễ đọc, thoáng mắt' },
  ];

  // Tab 4: Models state (FR-021 to FR-026, FR-035 to FR-039)
  const [models, setModels] = useState<AgentModel[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelFilterStatus, setModelFilterStatus] = useState<'ALL' | 'ACTIVE' | 'INACTIVE' | 'ARCHIVED'>('ALL');
  const [modelFilterProvider, setModelFilterProvider] = useState<string>('ALL');
  const [modelSearchQuery, setModelSearchQuery] = useState<string>('');
  const [modelSort, setModelSort] = useState<'name_asc' | 'latency_asc' | 'context_desc'>('name_asc');
  const [modelOnlyWithKey, setModelOnlyWithKey] = useState<boolean>(false);
  const [searchLatencyMs, setSearchLatencyMs] = useState<number | null>(null);

  const [testingModelId, setTestingModelId] = useState<string | null>(null);
  const [togglingModelId, setTogglingModelId] = useState<string | null>(null);
  const [settingDefaultId, setSettingDefaultId] = useState<string | null>(null);

  // Modal Create state (FR-035, OP-022)
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [createModelForm, setCreateModelForm] = useState({
    id: '',
    name: '',
    provider: 'google',
    context_window: 128000,
    max_tokens: 4096,
    supports_streaming: true
  });
  const [creatingModel, setCreatingModel] = useState<boolean>(false);

  // Modal Edit state (FR-036, OP-023)
  const [editingModel, setEditingModel] = useState<AgentModel | null>(null);
  const [editModelForm, setEditModelForm] = useState({
    name: '',
    context_window: 128000,
    max_tokens: 4096,
    supports_streaming: true
  });
  const [updatingModel, setUpdatingModel] = useState<boolean>(false);

  // Confirm Archive Modal state (FR-039, OP-025, BR-023)
  const [confirmArchiveModel, setConfirmArchiveModel] = useState<AgentModel | null>(null);
  const [archivingModelId, setArchivingModelId] = useState<string | null>(null);

  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 4000);
  };

  // Fetch initial profile & stats
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await fetch('/api/v1/users/me');
        if (!res.ok) {
          if (res.status === 401) {
            router.push('/login');
            return;
          }
          throw new Error('Failed to load profile details.');
        }
        const data = await res.json();
        const u = data.user;
        setUser(u);
        setStats(data.stats || { total_conversations: 0, total_messages: 0 });

        // Populate forms
        setFullName(u.full_name || '');
        setUsername(u.username || '');
        setBio(u.bio || '');
        setPhoneNumber(u.phone_number || '');
        setAge(u.age !== null && u.age !== undefined ? String(u.age) : '');
        setOccupation(u.occupation || '');
        setInterests(u.interests || '');
        setJapaneseLevel(u.japanese_level || 'CHUA_HOC');
        setLearningGoal(u.learning_goal || '');
        setAvatarUrl(u.avatar_url || '');
        setThemePreference(u.theme_preference || 'DARK');
        setLanguagePreference(u.language_preference || 'vi');
        setCustomBgUrl(u.custom_bg_url || '');
        setBgOpacity(u.bg_opacity !== undefined && u.bg_opacity !== null ? u.bg_opacity : 90);
        setBgBlur(u.bg_blur !== undefined && u.bg_blur !== null ? u.bg_blur : 12);
        setAccentColor(u.accent_color || 'emerald');
        setUiFontSize((u.ui_font_size as any) || 'medium');

        // Apply theme
        applyTheme(u.theme_preference || 'DARK');
      } catch (err: any) {
        showToast('error', err.message || 'Server connection error.');
      } finally {
        setLoadingInitial(false);
      }
    };

    fetchProfile();
  }, [router]);



  // Read URL query parameter ?tab=... on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get('tab');

      if (tabParam === 'models' || tabParam === 'security' || tabParam === 'preferences' || tabParam === 'profile' || tabParam === 'api-keys') {
        setActiveTab(tabParam as any);
      }
    }
  }, []);



  const fetchModels = async (searchQ?: string) => {
    try {
      setLoadingModels(true);
      const q = searchQ !== undefined ? searchQ : modelSearchQuery;
      const params = new URLSearchParams();
      if (q && q.trim()) params.append('q', q.trim());
      if (modelFilterProvider && modelFilterProvider !== 'ALL') params.append('provider', modelFilterProvider);
      if (modelFilterStatus && modelFilterStatus !== 'ALL') params.append('status', modelFilterStatus);
      if (modelSort) params.append('sort', modelSort);
      if (modelOnlyWithKey) params.append('has_api_key', 'true');

      const res = await fetch(`/api/v1/models/search?${params.toString()}`);
      if (!res.ok) {
        throw new Error('Failed to load models list from server.');
      }
      const data: ModelSearchResponse = await res.json();
      setModels(data.items);
      setSearchLatencyMs(data.execution_time_ms);
    } catch (err: any) {
      showToast('error', err.message || 'Error loading models list.');
    } finally {
      setLoadingModels(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'models') {
      fetchModels();
    }
  }, [activeTab, modelFilterStatus, modelFilterProvider, modelSort, modelOnlyWithKey]);

  useEffect(() => {
    if (activeTab !== 'models') return;
    const timer = setTimeout(() => {
      fetchModels(modelSearchQuery);
    }, 250);
    return () => clearTimeout(timer);
  }, [modelSearchQuery]);

  const handleTestConnection = async (model: AgentModel) => {
    setTestingModelId(model.id);
    try {
      const res = await fetch(`/api/v1/models/${model.id}/test`, {
        method: 'POST'
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Connection verification failed.');
      }
      setModels(prev =>
        prev.map(m => (m.id === model.id ? { ...m, latency_ms: data.latency_ms, last_checked_at: data.tested_at } : m))
      );
      showToast('success', `Latency: ${data.latency_ms} ms (Round-trip verified)`);
    } catch (err: any) {
      showToast('error', err.message || 'Connection test error.');
    } finally {
      setTestingModelId(null);
    }
  };

  const handleActivateModel = async (model: AgentModel) => {
    setTogglingModelId(model.id);
    try {
      const res = await fetch(`/api/v1/models/${model.id}/activate`, {
        method: 'PATCH'
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to activate model.');
      }
      setModels(prev =>
        prev.map(m => (m.id === model.id ? { ...m, status: 'ACTIVE' } : m))
      );
      showToast('success', data.message || `Activated ${model.name}.`);
    } catch (err: any) {
      showToast('error', err.message || 'Error activating model.');
    } finally {
      setTogglingModelId(null);
    }
  };

  const handleDeactivateModel = async (model: AgentModel) => {
    if (model.is_default) {
      showToast('error', `Cannot deactivate '${model.name}' because it is the system default model (BR-013). Set another model as default first.`);
      return;
    }
    setTogglingModelId(model.id);
    try {
      const res = await fetch(`/api/v1/models/${model.id}/deactivate`, {
        method: 'PATCH'
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to deactivate model.');
      }
      setModels(prev =>
        prev.map(m => (m.id === model.id ? { ...m, status: 'INACTIVE' } : m))
      );
      showToast('success', data.message || `Model moved to INACTIVE status (BR-012).`);
    } catch (err: any) {
      showToast('error', err.message || 'Error deactivating model.');
    } finally {
      setTogglingModelId(null);
    }
  };

  const handleSetDefaultModel = async (model: AgentModel) => {
    if (model.status !== 'ACTIVE') {
      showToast('error', `Only models in ACTIVE status can be designated as default (BR-013). Please activate the model first.`);
      return;
    }
    setSettingDefaultId(model.id);
    try {
      const res = await fetch('/api/v1/models/default', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: model.id })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to set default model.');
      }
      setModels(prev =>
        prev.map(m => ({ ...m, is_default: m.id === model.id }))
      );
      showToast('success', data.message || `Set '${model.name}' as default model.`);
    } catch (err: any) {
      showToast('error', err.message || 'Error setting default model.');
    } finally {
      setSettingDefaultId(null);
    }
  };

  // FR-035: Register new model
  const handleCreateModel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createModelForm.id.trim() || !createModelForm.name.trim()) {
      showToast('error', 'Please provide both Model ID and Display Name.');
      return;
    }
    if (createModelForm.max_tokens > createModelForm.context_window) {
      showToast('error', 'Max tokens cannot exceed context window (BR-024).');
      return;
    }
    if (createModelForm.context_window < 1000 || createModelForm.max_tokens < 256) {
      showToast('error', 'Safety boundary: Context Window >= 1,000 and Max Tokens >= 256 (BR-024).');
      return;
    }

    setCreatingModel(true);
    try {
      const res = await fetch('/api/v1/models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(createModelForm)
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to register model.');
      }
      showToast('success', `Model ${createModelForm.name} registered successfully.`);
      setShowCreateModal(false);
      setCreateModelForm({
        id: '',
        name: '',
        provider: 'google',
        context_window: 128000,
        max_tokens: 4096,
        supports_streaming: true
      });
      await fetchModels();
    } catch (err: any) {
      showToast('error', err.message || 'Error registering model.');
    } finally {
      setCreatingModel(false);
    }
  };

  // FR-036: Edit model configuration
  const openEditModal = (model: AgentModel) => {
    setEditingModel(model);
    setEditModelForm({
      name: model.name,
      context_window: model.context_window,
      max_tokens: model.max_tokens,
      supports_streaming: model.supports_streaming
    });
  };

  const handleUpdateModel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingModel) return;
    if (!editModelForm.name.trim()) {
      showToast('error', 'Model name cannot be empty.');
      return;
    }
    if (editModelForm.max_tokens > editModelForm.context_window) {
      showToast('error', 'Max tokens cannot exceed context window (BR-024).');
      return;
    }
    if (editModelForm.context_window < 1000 || editModelForm.max_tokens < 256) {
      showToast('error', 'Safety boundary: Context Window >= 1,000 and Max Tokens >= 256 (BR-024).');
      return;
    }

    setUpdatingModel(true);
    try {
      const res = await fetch(`/api/v1/models/${editingModel.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editModelForm)
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to update model configuration.');
      }
      showToast('success', `Configuration updated for ${editingModel.id}.`);
      setEditingModel(null);
      await fetchModels();
    } catch (err: any) {
      showToast('error', err.message || 'Error updating model.');
    } finally {
      setUpdatingModel(false);
    }
  };

  // FR-039: Soft archive model
  const handleArchiveModel = async (model: AgentModel) => {
    if (model.is_default) {
      showToast('error', `Cannot archive '${model.name}' because it is the system default model (BR-023). Please designate an alternative model as default first.`);
      return;
    }
    setArchivingModelId(model.id);
    try {
      const res = await fetch(`/api/v1/models/${model.id}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to archive model.');
      }
      showToast('success', data.message || `Model archived successfully.`);
      setConfirmArchiveModel(null);
      await fetchModels();
    } catch (err: any) {
      showToast('error', err.message || 'Error archiving model.');
    } finally {
      setArchivingModelId(null);
    }
  };

  const getProviderMeta = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'google':
        return {
          label: 'Google Gemini',
          textColor: '#60a5fa',
          border: 'rgba(66, 133, 244, 0.35)',
          badgeBg: 'rgba(59, 130, 246, 0.15)'
        };
      case 'openai':
        return {
          label: 'OpenAI',
          textColor: '#34d399',
          border: 'rgba(16, 185, 129, 0.35)',
          badgeBg: 'rgba(16, 185, 129, 0.15)'
        };
      case 'anthropic':
        return {
          label: 'Anthropic Claude',
          textColor: '#fbbf24',
          border: 'rgba(245, 158, 11, 0.35)',
          badgeBg: 'rgba(245, 158, 11, 0.15)'
        };
      case 'groq':
        return {
          label: 'Groq LPU',
          textColor: '#fb923c',
          border: 'rgba(249, 115, 22, 0.35)',
          badgeBg: 'rgba(249, 115, 22, 0.15)'
        };
      case 'ollama':
        return {
          label: 'Ollama Local',
          textColor: '#a78bfa',
          border: 'rgba(139, 92, 246, 0.35)',
          badgeBg: 'rgba(139, 92, 246, 0.15)'
        };
      default:
        return {
          label: provider.toUpperCase(),
          textColor: 'var(--text-secondary)',
          border: 'var(--border-subtle)',
          badgeBg: 'rgba(255, 255, 255, 0.08)'
        };
    }
  };

  const getStatusMeta = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return {
          label: 'Active',
          badgeBg: 'rgba(62, 207, 142, 0.15)',
          badgeBorder: 'rgba(62, 207, 142, 0.35)',
          textColor: 'var(--accent)',
          dotColor: 'var(--accent)'
        };
      case 'INACTIVE':
        return {
          label: 'Inactive',
          badgeBg: 'rgba(148, 163, 184, 0.1)',
          badgeBorder: 'rgba(148, 163, 184, 0.25)',
          textColor: '#94a3b8',
          dotColor: '#64748b'
        };
      case 'DEGRADED':
        return {
          label: 'Degraded',
          badgeBg: 'rgba(245, 158, 11, 0.15)',
          badgeBorder: 'rgba(245, 158, 11, 0.4)',
          textColor: '#fbbf24',
          dotColor: '#f59e0b'
        };
      case 'ARCHIVED':
        return {
          label: 'Archived',
          badgeBg: 'rgba(239, 68, 68, 0.12)',
          badgeBorder: 'rgba(239, 68, 68, 0.35)',
          textColor: '#f87171',
          dotColor: '#ef4444'
        };
      default:
        return {
          label: status,
          badgeBg: 'rgba(255, 255, 255, 0.08)',
          badgeBorder: 'var(--border-subtle)',
          textColor: 'var(--text-secondary)',
          dotColor: '#94a3b8'
        };
    }
  };

  const applyTheme = (theme: 'DARK' | 'LIGHT' | 'SYSTEM') => {
    if (typeof document !== 'undefined') {
      if (theme === 'LIGHT') {
        document.documentElement.setAttribute('data-theme', 'light');
      } else if (theme === 'DARK') {
        document.documentElement.removeAttribute('data-theme');
      } else {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (prefersDark) {
          document.documentElement.removeAttribute('data-theme');
        } else {
          document.documentElement.setAttribute('data-theme', 'light');
        }
      }
    }
  };

  // Password strength calculation
  const getPasswordStrength = (pass: string) => {
    if (!pass) return { score: 0, label: '', color: 'transparent' };
    let score = 0;
    if (pass.length >= 8) score += 1;
    if (pass.length >= 12) score += 1;
    if (/[A-Z]/.test(pass) && /[a-z]/.test(pass)) score += 1;
    if (/[0-9]/.test(pass)) score += 1;
    if (/[^A-Za-z0-9]/.test(pass)) score += 1;

    if (score <= 2) return { score: 33, label: 'Weak', color: '#ef4444' };
    if (score <= 4) return { score: 66, label: 'Fair', color: '#f59e0b' };
    return { score: 100, label: 'Strong', color: 'var(--accent)' };
  };

  // 1. Submit Profile Update
  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);

    try {
      const res = await fetch('/api/v1/users/me/profile', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName.trim(),
          username: username.trim() || null,
          bio: bio.trim(),
          phone_number: phoneNumber.trim(),
          age: age.trim() ? parseInt(age.trim(), 10) : null,
          occupation: occupation.trim() || null,
          interests: interests.trim() || null,
          japanese_level: japaneseLevel || 'CHUA_HOC',
          learning_goal: learningGoal.trim() || null
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to update profile.');
      }

      setUser(prev => prev ? { ...prev, ...data.user } : data.user);
      showToast('success', 'Profile updated successfully.');
    } catch (err: any) {
      showToast('error', err.message || 'Error updating profile.');
    } finally {
      setSavingProfile(false);
    }
  };

  // 2. Submit Avatar Update
  const handleUpdateAvatar = async () => {
    if (!avatarUrl.trim()) {
      showToast('error', 'Please enter a valid image URL.');
      return;
    }

    try {
      const res = await fetch('/api/v1/users/me/avatar', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ avatar_url: avatarUrl.trim() })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to update avatar.');

      setUser(prev => prev ? { ...prev, avatar_url: avatarUrl.trim() } : null);
      setShowAvatarEdit(false);
      showToast('success', 'Avatar updated successfully.');
    } catch (err: any) {
      showToast('error', err.message || 'Error updating avatar.');
    }
  };

  // 3. Submit Change Email
  const handleChangeEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEmail.trim() || !emailCurrentPassword) {
      showToast('error', 'Please enter your new email address and current password.');
      return;
    }

    setSavingEmail(true);
    try {
      const res = await fetch('/api/v1/users/me/change-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_email: newEmail.trim(),
          current_password: emailCurrentPassword
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to change email address.');

      setUser(prev => prev ? { ...prev, email: data.email } : null);
      setNewEmail('');
      setEmailCurrentPassword('');
      showToast('success', 'Email address updated successfully.');
    } catch (err: any) {
      showToast('error', err.message || 'Error changing email.');
    } finally {
      setSavingEmail(false);
    }
  };

  // 4. Submit Change Password
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword || !newPassword) {
      showToast('error', 'Please enter your current password and new password.');
      return;
    }

    if (newPassword.length < 8) {
      showToast('error', 'New password must be at least 8 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      showToast('error', 'New password confirmation does not match.');
      return;
    }

    setSavingPassword(true);
    try {
      const res = await fetch('/api/v1/users/me/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to change password.');

      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      showToast('success', 'Password updated successfully. Session refreshed.');
    } catch (err: any) {
      showToast('error', err.message || 'Error changing password.');
    } finally {
      setSavingPassword(false);
    }
  };

  // 5. Submit Preferences Update (FR-020, UC-015, UI Personalization)
  const handleUpdatePreferences = async (overrides?: Partial<{
    theme: 'DARK' | 'LIGHT' | 'SYSTEM';
    lang: 'vi' | 'en';
    bgUrl: string;
    opacity: number;
    blur: number;
    accent: string;
    fontSize: 'small' | 'medium' | 'large';
  }>) => {
    const nextTheme = overrides?.theme !== undefined ? overrides.theme : themePreference;
    const nextLang = overrides?.lang !== undefined ? overrides.lang : languagePreference;
    const nextBgUrl = overrides?.bgUrl !== undefined ? overrides.bgUrl : customBgUrl;
    const nextOpacity = overrides?.opacity !== undefined ? overrides.opacity : bgOpacity;
    const nextBlur = overrides?.blur !== undefined ? overrides.blur : bgBlur;
    const nextAccent = overrides?.accent !== undefined ? overrides.accent : accentColor;
    const nextFontSize = overrides?.fontSize !== undefined ? overrides.fontSize : uiFontSize;

    if (overrides?.theme !== undefined) setThemePreference(nextTheme);
    if (overrides?.lang !== undefined) setLanguagePreference(nextLang);
    if (overrides?.bgUrl !== undefined) setCustomBgUrl(nextBgUrl);
    if (overrides?.opacity !== undefined) setBgOpacity(nextOpacity);
    if (overrides?.blur !== undefined) setBgBlur(nextBlur);
    if (overrides?.accent !== undefined) setAccentColor(nextAccent);
    if (overrides?.fontSize !== undefined) setUiFontSize(nextFontSize);

    applyTheme(nextTheme);

    setSavingPreferences(true);
    try {
      const res = await fetch('/api/v1/users/me/preferences', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          theme_preference: nextTheme,
          language_preference: nextLang,
          custom_bg_url: nextBgUrl,
          bg_opacity: nextOpacity,
          bg_blur: nextBlur,
          accent_color: nextAccent,
          ui_font_size: nextFontSize
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Không thể lưu cài đặt tùy chọn.');

      await refreshUser();
      showToast('success', 'Đã lưu cấu hình tùy chỉnh giao diện thành công.');
    } catch (err: any) {
      showToast('error', err.message || 'Lỗi lưu tùy chọn giao diện.');
    } finally {
      setSavingPreferences(false);
    }
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      showToast('error', 'Chỉ hỗ trợ tệp hình ảnh hợp lệ (PNG, JPG, WebP).');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      showToast('error', 'Kích thước tệp ảnh tối đa là 5MB.');
      return;
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      const result = event.target?.result as string;
      if (result) {
        setCustomBgUrl(result);
        showToast('success', 'Đã nạp ảnh thành công. Nhấn "Lưu Thay Đổi Giao Diện" để áp dụng.');
      }
    };
    reader.readAsDataURL(file);
  };

  if (loadingInitial) {
    return (
      <div style={{
        minHeight: '60vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--text-secondary)'
      }}>
        <div style={{ textAlign: 'center' }}>
          <Icon name="settings" size={32} style={{ margin: '0 auto 12px', opacity: 0.6 }} />
          <p style={{ fontSize: '0.9rem' }}>Loading account settings...</p>
        </div>
      </div>
    );
  }

  const pwdStrength = getPasswordStrength(newPassword);

  return (
    <div
      className="custom-scrollbar"
      style={{
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: '100%',
        flex: 1,
        overflowY: 'auto',
      }}
    >
      {/* Toast Notification */}
      {toast && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          padding: '12px 18px',
          borderRadius: 'var(--radius-md)',
          background: toast.type === 'success' ? '#065f46' : '#991b1b',
          color: '#ffffff',
          fontWeight: 600,
          fontSize: '0.88rem',
          boxShadow: '0 10px 25px rgba(0,0,0,0.4)',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <Icon name={toast.type === 'success' ? 'check' : 'alert'} size={16} />
          <span>{toast.message}</span>
        </div>
      )}

      {/* Main Container */}
      <div style={{ width: '100%', maxWidth: '840px' }}>
        {/* Top Header Navigation */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1.5rem'
        }}>
          <Link
            href="/chat"
            className="btn btn-secondary"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <Icon name="chevronLeft" size={14} />
            <span>Back to Chat</span>
          </Link>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Version: <strong style={{ color: 'var(--text-secondary)' }}>1.0.0</strong>
          </div>
        </div>

        {/* User Summary Card */}
        <div style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)',
          padding: '1.5rem',
          marginBottom: '1.5rem',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1.25rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            {/* Avatar display */}
            <div style={{ position: 'relative' }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: user?.avatar_url ? `url(${user.avatar_url}) center/cover no-repeat` : 'var(--bg-hover)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.5rem',
                fontWeight: 700,
                color: 'var(--accent)',
                border: '2px solid var(--border-subtle)'
              }}>
                {!user?.avatar_url && (user?.full_name?.[0] || user?.email?.[0] || 'U').toUpperCase()}
              </div>
            </div>

            <div>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                {user?.full_name || 'User'}
              </h1>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', gap: '10px', alignItems: 'center' }}>
                <span>{user?.email}</span>
                {user?.username && (
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)',
                    background: 'rgba(62, 207, 142, 0.12)',
                    color: 'var(--accent)',
                    fontSize: '0.75rem',
                    fontWeight: 600
                  }}>
                    @{user.username}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Quick Stats Badges */}
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{
              background: 'var(--bg-base)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 16px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--accent)' }}>
                {stats.total_conversations}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Conversations</div>
            </div>
            <div style={{
              background: 'var(--bg-base)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 16px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--accent)' }}>
                {stats.total_messages}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Messages Sent</div>
            </div>
          </div>
        </div>

        {/* Tab Navigation Buttons */}
        <div className="segmented-control" style={{ marginBottom: '1.5rem', width: '100%', overflowX: 'auto' }}>
          <button
            type="button"
            className={`segmented-item ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <Icon name="user" size={14} />
            <span>Profile</span>
          </button>

          <button
            type="button"
            className={`segmented-item ${activeTab === 'security' ? 'active' : ''}`}
            onClick={() => setActiveTab('security')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <Icon name="shield" size={14} />
            <span>Security</span>
          </button>

          <button
            type="button"
            className={`segmented-item ${activeTab === 'preferences' ? 'active' : ''}`}
            onClick={() => setActiveTab('preferences')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <Icon name="settings" size={14} />
            <span>Preferences</span>
          </button>

          

          <button
            type="button"
            className={`segmented-item ${activeTab === 'models' ? 'active' : ''}`}
            onClick={() => setActiveTab('models')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <Icon name="cpu" size={14} />
            <span>AI Models</span>
          </button>

          <button
            type="button"
            id="tab-api-keys"
            className={`segmented-item ${activeTab === 'api-keys' ? 'active' : ''}`}
            onClick={() => setActiveTab('api-keys')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <Icon name="key" size={14} />
            <span>API Keys</span>
          </button>
        </div>

        {/* ============================================================ */}
        {/* TAB 1: PROFILE                                               */}
        {/* ============================================================ */}
        {activeTab === 'profile' && (
          <div className="card" style={{ padding: '1.75rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1.25rem', color: 'var(--text-primary)' }}>
              Personal Profile
            </h2>

            {/* Avatar Setting Section */}
            <div style={{
              background: 'var(--bg-base)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '1.25rem',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '1rem'
            }}>
              <div>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px' }}>
                  Avatar Image
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Supports HTTPS image URLs.
                </div>
              </div>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowAvatarEdit(!showAvatarEdit)}
              >
                {showAvatarEdit ? 'Close' : 'Change Avatar'}
              </button>

              {showAvatarEdit && (
                <div style={{ width: '100%', marginTop: '0.75rem', display: 'flex', gap: '8px' }}>
                  <input
                    type="url"
                    placeholder="Enter image URL (https://...)"
                    value={avatarUrl}
                    onChange={(e) => setAvatarUrl(e.target.value)}
                    className="input"
                    style={{ flex: 1 }}
                  />
                  <button
                    type="button"
                    onClick={handleUpdateAvatar}
                    className="btn btn-primary"
                  >
                    Save Image
                  </button>
                </div>
              )}
            </div>

            {/* Profile Form */}
            <form onSubmit={handleUpdateProfile}>
              {/* Row 1: Full Name & Username */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Jane Doe"
                    className="input"
                    style={{ width: '100%' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Username
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="janedoe"
                    className="input"
                    style={{ width: '100%' }}
                  />
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                    3-30 characters (letters, numbers, underscores _, dots .)
                  </span>
                </div>
              </div>

              {/* Row 2: Phone Number & Age */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="+1 (555) 000-0000"
                    className="input"
                    style={{ width: '100%' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Age
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={120}
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    placeholder="e.g. 25"
                    className="input"
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              {/* Row 3: Occupation & Japanese Level */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Occupation
                  </label>
                  <input
                    type="text"
                    maxLength={100}
                    value={occupation}
                    onChange={(e) => setOccupation(e.target.value)}
                    placeholder="e.g. Software Engineer, Student"
                    className="input"
                    style={{ width: '100%' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Japanese Level
                  </label>
                  <select
                    value={japaneseLevel}
                    onChange={(e) => setJapaneseLevel(e.target.value)}
                    className="input"
                    style={{ width: '100%', height: '38px' }}
                  >
                    <option value="CHUA_HOC">Beginner / Not studied yet</option>
                    <option value="N5">JLPT N5 (Basic Elementary)</option>
                    <option value="N4">JLPT N4 (Elementary)</option>
                    <option value="N3">JLPT N3 (Intermediate)</option>
                    <option value="N2">JLPT N2 (Upper Intermediate)</option>
                    <option value="N1">JLPT N1 (Advanced)</option>
                  </select>
                </div>
              </div>

              {/* Row 4: Learning Goal & Interests */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Learning Goal
                  </label>
                  <input
                    type="text"
                    maxLength={255}
                    value={learningGoal}
                    onChange={(e) => setLearningGoal(e.target.value)}
                    placeholder="e.g. Daily conversation, JLPT N2, Work in Japan"
                    className="input"
                    style={{ width: '100%' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Interests &amp; Hobbies
                  </label>
                  <input
                    type="text"
                    maxLength={255}
                    value={interests}
                    onChange={(e) => setInterests(e.target.value)}
                    placeholder="e.g. Anime, Manga, Tokyo travel, Technology"
                    className="input"
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              {/* Row 5: Bio */}
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Bio</label>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{bio.length}/500</span>
                </div>
                <textarea
                  value={bio}
                  maxLength={500}
                  onChange={(e) => setBio(e.target.value)}
                  placeholder="Tell us about yourself..."
                  rows={4}
                  className="input"
                  style={{ width: '100%', resize: 'vertical' }}
                />
              </div>

              <button
                type="submit"
                disabled={savingProfile}
                className="btn btn-primary"
              >
                {savingProfile ? 'Saving...' : 'Save Profile'}
              </button>
            </form>
          </div>
        )}

        {/* ============================================================ */}
        {/* TAB 2: SECURITY & LOGIN                                      */}
        {/* ============================================================ */}
        {activeTab === 'security' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Card 1: Change Email */}
            <div className="card" style={{ padding: '1.75rem' }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
                Change Email Address
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
                Current email: <strong style={{ color: 'var(--text-primary)' }}>{user?.email}</strong>. Current password verification is required.
              </p>

              <form onSubmit={handleChangeEmail}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      New Email Address
                    </label>
                    <input
                      type="email"
                      value={newEmail}
                      onChange={(e) => setNewEmail(e.target.value)}
                      placeholder="new.email@example.com"
                      required
                      className="input"
                      style={{ width: '100%' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      Current Password
                    </label>
                    <input
                      type="password"
                      value={emailCurrentPassword}
                      onChange={(e) => setEmailCurrentPassword(e.target.value)}
                      placeholder="Enter current password"
                      required
                      className="input"
                      style={{ width: '100%' }}
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={savingEmail}
                  className="btn btn-primary"
                >
                  {savingEmail ? 'Verifying...' : 'Update Email'}
                </button>
              </form>
            </div>

            {/* Card 2: Change Password */}
            <div className="card" style={{ padding: '1.75rem' }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
                Change Password
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
                After updating your password, active sessions will receive refreshed security credentials.
              </p>

              <form onSubmit={handleChangePassword}>
                <div style={{ marginBottom: '1.25rem' }}>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Current Password
                  </label>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Your current password"
                    required
                    className="input"
                    style={{ width: '100%', maxWidth: '420px' }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem', marginBottom: '0.75rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      New Password
                    </label>
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="At least 8 characters"
                      required
                      className="input"
                      style={{ width: '100%' }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Re-enter new password"
                      required
                      className="input"
                      style={{ width: '100%' }}
                    />
                  </div>
                </div>

                {/* Password Strength Meter */}
                {newPassword && (
                  <div style={{ marginBottom: '1.25rem', maxWidth: '420px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Password Strength:</span>
                      <span style={{ color: pwdStrength.color, fontWeight: 600 }}>{pwdStrength.label}</span>
                    </div>
                    <div style={{ height: '4px', background: 'var(--bg-hover)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%',
                        width: `${pwdStrength.score}%`,
                        background: pwdStrength.color,
                        transition: 'all 0.3s ease'
                      }} />
                    </div>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={savingPassword}
                  className="btn btn-primary"
                >
                  {savingPassword ? 'Updating...' : 'Update Password'}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* TAB 3: PREFERENCES (FR-020, UC-015, UI PERSONALIZATION)      */}
        {/* ============================================================ */}
        {activeTab === 'preferences' && (
          <div className="card" style={{ padding: '1.75rem' }}>
            <div style={{ marginBottom: '1.5rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                Tùy Chỉnh Giao Diện & Cá Nhân Hóa
              </h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Tùy biến hình nền không gian học tập, độ trong suốt kính mờ, bảng màu chủ đạo và mật độ hiển thị theo sở thích.
              </p>
            </div>

            {/* Section 1: Theme Mode */}
            <div style={{ marginBottom: '2rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '10px' }}>
                Chế độ màu giao diện (Theme Mode)
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
                <div
                  onClick={() => handleUpdatePreferences({ theme: 'DARK' })}
                  style={{
                    padding: '1.25rem',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-base)',
                    border: themePreference === 'DARK' ? '2px solid var(--accent)' : '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                    textAlign: 'center',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>Dark Mode</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>Bề mặt tối trung tính dịu mắt</div>
                </div>

                <div
                  onClick={() => handleUpdatePreferences({ theme: 'LIGHT' })}
                  style={{
                    padding: '1.25rem',
                    borderRadius: 'var(--radius-md)',
                    background: '#f8fafc',
                    color: '#0f172a',
                    border: themePreference === 'LIGHT' ? '2px solid var(--accent)' : '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                    textAlign: 'center',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#0f172a' }}>Light Mode</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>Bảng màu sáng tương phản cao</div>
                </div>

                <div
                  onClick={() => handleUpdatePreferences({ theme: 'SYSTEM' })}
                  style={{
                    padding: '1.25rem',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-base)',
                    border: themePreference === 'SYSTEM' ? '2px solid var(--accent)' : '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                    textAlign: 'center',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>Theo hệ điều hành</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>Tự động đồng bộ cài đặt OS</div>
                </div>
              </div>
            </div>

            {/* Section 2: Accent Color Palette */}
            <div style={{ marginBottom: '2rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Màu chủ đạo (Accent Palette)
              </label>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                Thay đổi màu các nút bấm, biểu tượng nổi bật và viền nhấn trong toàn bộ ứng dụng.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.75rem' }}>
                {ACCENT_PRESETS.map((acc) => {
                  const isSelected = accentColor === acc.id;
                  return (
                    <div
                      key={acc.id}
                      onClick={() => handleUpdatePreferences({ accent: acc.id })}
                      style={{
                        padding: '10px 12px',
                        borderRadius: 'var(--radius-md)',
                        background: isSelected ? 'var(--bg-selected)' : 'var(--bg-base)',
                        border: isSelected ? `2px solid ${acc.hex}` : '1px solid var(--border-subtle)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <div style={{ width: '14px', height: '14px', borderRadius: '50%', backgroundColor: acc.hex, flexShrink: 0, boxShadow: isSelected ? `0 0 8px ${acc.hex}` : 'none' }} />
                      <div>
                        <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>{acc.name}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{acc.desc}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Section 3: Custom Wallpaper */}
            <div style={{ marginBottom: '2rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Hình nền website tùy chỉnh (Custom Wallpaper)
                </label>
                {customBgUrl && (
                  <button
                    type="button"
                    onClick={() => handleUpdatePreferences({ bgUrl: '' })}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--danger)',
                      fontSize: '0.78rem',
                      cursor: 'pointer',
                      padding: 0
                    }}
                  >
                    Xóa hình nền
                  </button>
                )}
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                Cung cấp URL hình ảnh hoặc tải ảnh trực tiếp từ máy tính để làm hình nền cho không gian học tập.
              </p>

              <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
                <input
                  type="text"
                  value={customBgUrl.startsWith('data:image') ? '[Tệp ảnh đã tải từ máy tính]' : customBgUrl}
                  disabled={customBgUrl.startsWith('data:image')}
                  onChange={(e) => setCustomBgUrl(e.target.value)}
                  placeholder="https://images.unsplash.com/... (URL hình ảnh)"
                  className="input"
                  style={{ flex: 1, minWidth: '240px' }}
                />
                <label
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '0 14px',
                    height: '36px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-default)',
                    color: 'var(--text-primary)',
                    fontSize: '0.82rem',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    fontWeight: 500,
                    transition: 'background var(--transition-fast)'
                  }}
                >
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    style={{ display: 'none' }}
                  />
                  Tải ảnh từ máy
                </label>
              </div>

              {/* Preset Wallpaper Chips */}
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginRight: '4px' }}>Gợi ý hình nền Nhật Bản:</span>
                {WALLPAPER_PRESETS.map((wp) => {
                  const isActive = customBgUrl === wp.url;
                  return (
                    <button
                      key={wp.id}
                      type="button"
                      onClick={() => handleUpdatePreferences({ bgUrl: wp.url })}
                      style={{
                        padding: '4px 10px',
                        borderRadius: 'var(--radius-full)',
                        fontSize: '0.75rem',
                        fontWeight: isActive ? 600 : 400,
                        background: isActive ? 'var(--bg-selected)' : 'var(--bg-base)',
                        border: isActive ? '1px solid var(--accent)' : '1px solid var(--border-subtle)',
                        color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      {wp.label}
                    </button>
                  );
                })}
              </div>

              {/* Wallpaper Preview banner */}
              {customBgUrl && (
                <div
                  style={{
                    marginTop: '12px',
                    height: '80px',
                    borderRadius: 'var(--radius-md)',
                    backgroundImage: `url("${customBgUrl}")`,
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                    border: '1px solid var(--border-default)',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                >
                  <div
                    style={{
                      position: 'absolute',
                      bottom: '8px',
                      left: '8px',
                      background: 'rgba(0, 0, 0, 0.7)',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-xs)',
                      fontSize: '0.7rem',
                      color: '#ffffff'
                    }}
                  >
                    Xem trước hình nền
                  </div>
                </div>
              )}
            </div>

            {/* Section 4: Overlay & Glassmorphism Sliders */}
            <div style={{ marginBottom: '2rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.5rem' }}>
              {/* Slider 1: Opacity */}
              <div style={{ padding: '14px', background: 'var(--bg-base)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Độ đục lớp phủ (Layer Opacity)
                  </label>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>
                    {bgOpacity}%
                  </span>
                </div>
                <input
                  type="range"
                  min={20}
                  max={100}
                  step={5}
                  value={bgOpacity}
                  onChange={(e) => setBgOpacity(Number(e.target.value))}
                  onMouseUp={() => handleUpdatePreferences({ opacity: bgOpacity })}
                  onTouchEnd={() => handleUpdatePreferences({ opacity: bgOpacity })}
                  style={{ width: '100%', accentColor: 'var(--accent)', cursor: 'pointer' }}
                />
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                  Độ trong suốt của thanh điều hướng và khung nội dung trên ảnh nền (20% - 100%).
                </p>
              </div>

              {/* Slider 2: Blur */}
              <div style={{ padding: '14px', background: 'var(--bg-base)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Độ mờ kính (Backdrop Blur)
                  </label>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>
                    {bgBlur}px
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={40}
                  step={2}
                  value={bgBlur}
                  onChange={(e) => setBgBlur(Number(e.target.value))}
                  onMouseUp={() => handleUpdatePreferences({ blur: bgBlur })}
                  onTouchEnd={() => handleUpdatePreferences({ blur: bgBlur })}
                  style={{ width: '100%', accentColor: 'var(--accent)', cursor: 'pointer' }}
                />
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                  Hiệu ứng kính mờ (glassmorphism) làm nổi bật văn bản và hội thoại tiếng Nhật (0px - 40px).
                </p>
              </div>
            </div>

            {/* Section 5: UI Font Size / Density */}
            <div style={{ marginBottom: '2rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Cỡ chữ & Mật độ hiển thị (Layout Density)
              </label>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                Điều chỉnh tỉ lệ phông chữ và khoảng cách giao diện cho phù hợp với tầm nhìn.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
                {FONT_SIZE_PRESETS.map((fs) => {
                  const isSelected = uiFontSize === fs.id;
                  return (
                    <div
                      key={fs.id}
                      onClick={() => handleUpdatePreferences({ fontSize: fs.id as any })}
                      style={{
                        padding: '12px',
                        borderRadius: 'var(--radius-md)',
                        background: isSelected ? 'var(--bg-selected)' : 'var(--bg-base)',
                        border: isSelected ? '2px solid var(--accent)' : '1px solid var(--border-subtle)',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>{fs.label}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>{fs.desc}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Section 6: Language Selector */}
            <div style={{ marginBottom: '2rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
                Ngôn ngữ hiển thị (Interface Language)
              </label>
              <select
                value={languagePreference}
                onChange={(e) => handleUpdatePreferences({ lang: e.target.value as 'vi' | 'en' })}
                className="input"
                style={{ width: '100%', maxWidth: '280px', cursor: 'pointer' }}
              >
                <option value="vi">Tiếng Việt (Mặc định)</option>
                <option value="en">English</option>
              </select>
            </div>

            {/* Section 7: Save Preferences Action */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', borderTop: '1px solid var(--border-subtle)', paddingTop: '1.25rem' }}>
              <button
                type="button"
                onClick={() => handleUpdatePreferences()}
                disabled={savingPreferences}
                className="btn-primary"
                style={{
                  padding: '8px 20px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.85rem',
                  fontWeight: 500,
                  cursor: savingPreferences ? 'not-allowed' : 'pointer'
                }}
              >
                {savingPreferences ? 'Đang lưu tùy chỉnh...' : 'Lưu Thay Đổi Giao Diện'}
              </button>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* TAB 5: AI MODELS CATALOG (FR-021 TO FR-026, FR-035..39)      */}
        {/* ============================================================ */}
        {activeTab === 'models' && (
          <div className="card" style={{ padding: '1.75rem' }}>
            {/* Header: Title & Action Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  AI Models & Agent Catalog
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
                  Manage model lifecycles, provider mappings, latency verification, and dynamic context parameters.
                </p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(true)}
                  className="btn btn-primary"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                >
                  <Icon name="plus" size={14} />
                  <span>Add Model</span>
                </button>

                <button
                  type="button"
                  onClick={() => fetchModels()}
                  disabled={loadingModels}
                  className="btn btn-secondary"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                >
                  <Icon name="refresh" size={14} />
                  <span>{loadingModels ? 'Loading...' : 'Refresh'}</span>
                </button>
              </div>
            </div>

            {/* Instant Search Bar (FR-037, NFR-022) */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-base)',
              border: '1px solid var(--border-subtle)',
              marginBottom: '1rem'
            }}>
              <Icon name="search" size={16} style={{ color: 'var(--text-muted)' }} />
              <input
                type="text"
                value={modelSearchQuery}
                onChange={(e) => setModelSearchQuery(e.target.value)}
                placeholder="Search models by name or identifier (e.g. gemini, claude, gpt)..."
                style={{
                  flex: 1,
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  color: 'var(--text-primary)',
                  fontSize: '0.85rem'
                }}
              />
              {modelSearchQuery && (
                <button
                  type="button"
                  onClick={() => setModelSearchQuery('')}
                  title="Clear search"
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer'
                  }}
                >
                  <Icon name="close" size={14} />
                </button>
              )}
              {searchLatencyMs !== null && (
                <span className="badge badge-accent" style={{ whiteSpace: 'nowrap', fontSize: '0.72rem' }}>
                  Latency: {searchLatencyMs} ms (SLA &le; 200ms)
                </span>
              )}
            </div>

            {/* Multi-Attribute Filter & Sort Toolbar (FR-038) */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-base)',
              border: '1px solid var(--border-subtle)',
              marginBottom: '1.5rem'
            }}>
              {/* Status Filter Tabs */}
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {(['ALL', 'ACTIVE', 'INACTIVE', 'ARCHIVED'] as const).map(st => {
                  const label = st === 'ALL'
                    ? `All (${models.length})`
                    : st === 'ACTIVE'
                    ? `Active`
                    : st === 'INACTIVE'
                    ? `Inactive`
                    : `Archived`;
                  const isSelected = modelFilterStatus === st;
                  return (
                    <button
                      key={st}
                      type="button"
                      onClick={() => setModelFilterStatus(st)}
                      style={{
                        padding: '5px 12px',
                        borderRadius: 'var(--radius-full)',
                        fontSize: '0.78rem',
                        fontWeight: isSelected ? 600 : 500,
                        background: isSelected ? 'var(--accent)' : 'var(--bg-surface)',
                        border: '1px solid ' + (isSelected ? 'var(--accent)' : 'var(--border-subtle)'),
                        color: isSelected ? '#000000' : 'var(--text-secondary)',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>

              {/* Right Selectors: Provider, Sort, Key Toggle */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                {/* Provider Filter Select */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Provider:</span>
                  <select
                    value={modelFilterProvider}
                    onChange={(e) => setModelFilterProvider(e.target.value)}
                    className="input"
                    style={{ padding: '4px 8px', fontSize: '0.78rem', cursor: 'pointer' }}
                  >
                    <option value="ALL">All Providers</option>
                    <option value="google">Google Gemini</option>
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="groq">Groq</option>
                    <option value="ollama">Ollama</option>
                  </select>
                </div>

                {/* Sort Order Select */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Sort:</span>
                  <select
                    value={modelSort}
                    onChange={(e) => setModelSort(e.target.value as any)}
                    className="input"
                    style={{ padding: '4px 8px', fontSize: '0.78rem', cursor: 'pointer' }}
                  >
                    <option value="name_asc">Name (A-Z)</option>
                    <option value="latency_asc">Lowest Latency</option>
                    <option value="context_desc">Largest Context</option>
                  </select>
                </div>

                {/* Has API Key Toggle */}
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={modelOnlyWithKey}
                    onChange={(e) => setModelOnlyWithKey(e.target.checked)}
                    style={{ cursor: 'pointer' }}
                  />
                  <span>API Key Configured Only</span>
                </label>
              </div>
            </div>

            {/* Models Cards Grid */}
            {loadingModels && models.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                <Icon name="refresh" size={24} style={{ margin: '0 auto 8px', opacity: 0.6 }} />
                <div>Loading AI model catalog...</div>
              </div>
            ) : models.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)', background: 'var(--bg-base)', borderRadius: 'var(--radius-md)' }}>
                <Icon name="search" size={24} style={{ margin: '0 auto 8px', opacity: 0.6 }} />
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>No models match your criteria</div>
                <div style={{ fontSize: '0.82rem' }}>Try adjusting your search query, status filters, or provider selection.</div>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
                {models.map(m => {
                  const pMeta = getProviderMeta(m.provider);
                  const sMeta = getStatusMeta(m.status);
                  const isTesting = testingModelId === m.id;
                  const isToggling = togglingModelId === m.id;
                  const isSettingDef = settingDefaultId === m.id;
                  const isArchiving = archivingModelId === m.id;
                  const isArchived = m.status === 'ARCHIVED';

                  return (
                    <div
                      key={m.id}
                      style={{
                        borderRadius: 'var(--radius-md)',
                        background: 'var(--bg-base)',
                        border: m.is_default
                          ? '1px solid var(--accent)'
                          : isArchived
                          ? '1px dashed rgba(239, 68, 68, 0.3)'
                          : '1px solid var(--border-subtle)',
                        padding: '1.25rem',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        opacity: isArchived ? 0.75 : 1,
                        transition: 'border-color 0.15s ease'
                      }}
                    >
                      {/* Top: Header with Provider, Name & Status */}
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                          {/* Provider pill */}
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '2px 8px',
                            borderRadius: 'var(--radius-full)',
                            background: pMeta.badgeBg,
                            border: `1px solid ${pMeta.border}`,
                            fontSize: '0.72rem',
                            fontWeight: 600,
                            color: pMeta.textColor
                          }}>
                            {pMeta.label}
                          </span>

                          {/* Status & Default Badges */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            {m.is_default && (
                              <span style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                                padding: '2px 8px',
                                borderRadius: 'var(--radius-full)',
                                background: 'rgba(62, 207, 142, 0.12)',
                                border: '1px solid var(--accent)',
                                color: 'var(--accent)',
                                fontSize: '0.72rem',
                                fontWeight: 600
                              }}>
                                Default
                              </span>
                            )}
                            <span style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              padding: '2px 8px',
                              borderRadius: 'var(--radius-full)',
                              background: sMeta.badgeBg,
                              border: `1px solid ${sMeta.badgeBorder}`,
                              color: sMeta.textColor,
                              fontSize: '0.72rem',
                              fontWeight: 600
                            }}>
                              <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: sMeta.dotColor }} />
                              <span>{sMeta.label}</span>
                            </span>
                          </div>
                        </div>

                        {/* Model Title & ID */}
                        <div style={{ marginBottom: '12px' }}>
                          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px' }}>
                            {m.name}
                          </h3>
                          <div style={{ fontSize: '0.72rem', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                            ID: {m.id}
                          </div>
                        </div>

                        {/* Key Presence Indicator */}
                        <div style={{
                          padding: '6px 10px',
                          borderRadius: 'var(--radius-sm)',
                          background: m.has_api_key ? 'rgba(62, 207, 142, 0.08)' : 'rgba(245, 158, 11, 0.08)',
                          border: `1px solid ${m.has_api_key ? 'rgba(62, 207, 142, 0.2)' : 'rgba(245, 158, 11, 0.2)'}`,
                          fontSize: '0.72rem',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          marginBottom: '12px'
                        }}>
                          <span style={{ color: m.has_api_key ? 'var(--accent)' : '#fbbf24', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Icon name={m.has_api_key ? 'key' : 'alert'} size={12} />
                            <span>{m.has_api_key ? 'API Key configured in environment' : 'API Key not configured in environment'}</span>
                          </span>
                          {m.latency_ms ? (
                            <span style={{ color: 'var(--accent)', fontWeight: 600 }}>
                              {m.latency_ms} ms
                            </span>
                          ) : null}
                        </div>

                        {/* Technical Specs 2x2 Grid */}
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(2, 1fr)',
                          gap: '8px',
                          background: 'var(--bg-surface)',
                          borderRadius: 'var(--radius-sm)',
                          padding: '10px',
                          marginBottom: '14px',
                          fontSize: '0.75rem'
                        }}>
                          <div>
                            <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem' }}>Context Window</span>
                            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{m.context_window.toLocaleString()} tokens</span>
                          </div>
                          <div>
                            <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem' }}>Max Output</span>
                            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{m.max_tokens.toLocaleString()} tokens</span>
                          </div>
                          <div>
                            <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem' }}>Streaming SSE</span>
                            <span style={{ fontWeight: 600, color: m.supports_streaming ? 'var(--accent)' : 'var(--text-muted)' }}>
                              {m.supports_streaming ? 'Supported' : 'No'}
                            </span>
                          </div>
                          <div>
                            <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.7rem' }}>Last Checked</span>
                            <span style={{ fontWeight: 500, color: 'var(--text-secondary)' }}>
                              {m.last_checked_at ? new Date(m.last_checked_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) : 'Not checked'}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Actions Footer Toolbar */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
                        {/* Action Row 1: Ping Test & Edit Model */}
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button
                            type="button"
                            onClick={() => handleTestConnection(m)}
                            disabled={isTesting}
                            title="Verify connection and measure latency to provider API"
                            className="btn btn-secondary"
                            style={{ flex: 1, fontSize: '0.78rem', padding: '6px 8px' }}
                          >
                            <Icon name="play" size={12} />
                            <span>{isTesting ? 'Testing...' : 'Ping Test'}</span>
                          </button>

                          {/* Edit Button (FR-036) */}
                          <button
                            type="button"
                            onClick={() => openEditModal(m)}
                            title="Edit model technical parameters (FR-036)"
                            className="btn btn-secondary"
                            style={{ flex: 1, fontSize: '0.78rem', padding: '6px 8px' }}
                          >
                            <Icon name="edit" size={12} />
                            <span>Edit</span>
                          </button>
                        </div>

                        {/* Action Row 2: Toggle Status & Soft Archive */}
                        <div style={{ display: 'flex', gap: '8px' }}>
                          {m.status === 'ACTIVE' ? (
                            <button
                              type="button"
                              onClick={() => handleDeactivateModel(m)}
                              disabled={isToggling || m.is_default}
                              title={m.is_default ? 'Cannot deactivate the system default model (BR-013)' : 'Soft toggle to inactive state (BR-012)'}
                              className="btn btn-secondary"
                              style={{ flex: 1, fontSize: '0.78rem', padding: '6px 8px' }}
                            >
                              <Icon name="pause" size={12} />
                              <span>{isToggling ? 'Processing...' : 'Deactivate'}</span>
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => handleActivateModel(m)}
                              disabled={isToggling}
                              title="Activate model for chat sessions"
                              className="btn btn-secondary"
                              style={{ flex: 1, fontSize: '0.78rem', padding: '6px 8px' }}
                            >
                              <Icon name="play" size={12} />
                              <span>{isToggling ? 'Processing...' : isArchived ? 'Restore' : 'Activate'}</span>
                            </button>
                          )}

                          {/* Soft Archive Button (FR-039, BR-023) */}
                          <button
                            type="button"
                            onClick={() => setConfirmArchiveModel(m)}
                            disabled={m.is_default || isArchived || isArchiving}
                            title={
                              m.is_default
                                ? 'Cannot archive system default model (BR-023)'
                                : isArchived
                                ? 'Model is already archived'
                                : 'Soft archive model safely (FR-039)'
                            }
                            className="btn btn-danger"
                            style={{ flex: 1, fontSize: '0.78rem', padding: '6px 8px' }}
                          >
                            <Icon name="trash" size={12} />
                            <span>{isArchived ? 'Archived' : 'Archive'}</span>
                          </button>
                        </div>

                        {/* Action Row 3: Set Default (Active only) */}
                        {!m.is_default && !isArchived && (
                          <div style={{ display: 'flex', gap: '8px', marginTop: '2px' }}>
                            <button
                              type="button"
                              onClick={() => handleSetDefaultModel(m)}
                              disabled={isSettingDef || m.status !== 'ACTIVE'}
                              title={m.status !== 'ACTIVE' ? 'Only ACTIVE models can be set as default' : 'Set as default model for new chat sessions'}
                              className="btn btn-secondary"
                              style={{ width: '100%', fontSize: '0.75rem', padding: '5px 8px' }}
                            >
                              <Icon name="check" size={12} />
                              <span>{isSettingDef ? 'Setting...' : 'Set as Default'}</span>
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Invariant Policy Callout Box (BR-012, BR-022, BR-023, BR-024) */}
            <div style={{
              background: 'var(--bg-base)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '1.25rem',
              fontSize: '0.8rem',
              lineHeight: 1.6
            }}>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Icon name="shield" size={16} />
                <span>Operational Invariants & Data Integrity Rules</span>
              </div>
              <ul style={{ listStyleType: 'disc', paddingLeft: '1.25rem', color: 'var(--text-secondary)' }}>
                <li>
                  <strong style={{ color: 'var(--text-primary)' }}>BR-022 (Immutable ID & Provider):</strong> Model identifier and provider are immutable post-creation to safeguard foreign-key integrity in chat histories and telemetry logs.
                </li>
                <li>
                  <strong style={{ color: 'var(--text-primary)' }}>BR-023 (Default Model Protection):</strong> The active default model (<code>is_default = 1</code>) cannot be deactivated or archived. Designate an alternative active model as default first.
                </li>
                <li>
                  <strong style={{ color: 'var(--text-primary)' }}>BR-024 (Safety Boundaries):</strong> Model parameters must strictly satisfy <code>Context Window &ge; 1,000</code>, <code>Max Tokens &ge; 256</code>, and <code>Max Tokens &le; Context Window</code>.
                </li>
                <li>
                  <strong style={{ color: 'var(--text-primary)' }}>NFR-022 (Search & Filter SLA):</strong> Dynamic catalog queries must resolve within 200ms round-trip latency.
                </li>
              </ul>
            </div>

            {/* ============================================================ */}
            {/* MODAL 1: REGISTER NEW MODEL (FR-035, OP-022)                 */}
            {/* ============================================================ */}
            {showCreateModal && (
              <div style={{
                position: 'fixed',
                inset: 0,
                background: 'rgba(0, 0, 0, 0.75)',
                backdropFilter: 'blur(8px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000,
                padding: '1rem'
              }}>
                <div className="card" style={{
                  maxWidth: '500px',
                  width: '100%',
                  padding: '1.75rem'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      Register New AI Model (FR-035)
                    </h3>
                    <button
                      type="button"
                      onClick={() => setShowCreateModal(false)}
                      style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                    >
                      <Icon name="close" size={16} />
                    </button>
                  </div>

                  <form onSubmit={handleCreateModel}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
                      {/* Model ID */}
                      <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                          Model ID (Globally Unique) *
                        </label>
                        <input
                          type="text"
                          required
                          value={createModelForm.id}
                          onChange={(e) => setCreateModelForm(prev => ({ ...prev, id: e.target.value }))}
                          placeholder="e.g. claude-3-5-sonnet, gpt-4.5-turbo..."
                          className="input"
                          style={{ width: '100%', fontFamily: 'monospace' }}
                        />
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Model ID is immutable post-creation (BR-022).</span>
                      </div>

                      {/* Display Name */}
                      <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                          Display Name *
                        </label>
                        <input
                          type="text"
                          required
                          value={createModelForm.name}
                          onChange={(e) => setCreateModelForm(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="e.g. Anthropic Claude 3.5 Sonnet..."
                          className="input"
                          style={{ width: '100%' }}
                        />
                      </div>

                      {/* Provider */}
                      <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                          Provider *
                        </label>
                        <select
                          value={createModelForm.provider}
                          onChange={(e) => setCreateModelForm(prev => ({ ...prev, provider: e.target.value }))}
                          className="input"
                          style={{ width: '100%', cursor: 'pointer' }}
                        >
                          <option value="google">Google Gemini</option>
                          <option value="openai">OpenAI</option>
                          <option value="anthropic">Anthropic</option>
                          <option value="groq">Groq</option>
                          <option value="ollama">Ollama (Local)</option>
                        </select>
                      </div>

                      {/* Specs: Context & Max Tokens 2 Columns */}
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                        <div>
                          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                            Context Window (tokens)
                          </label>
                          <input
                            type="number"
                            min="1000"
                            value={createModelForm.context_window}
                            onChange={(e) => setCreateModelForm(prev => ({ ...prev, context_window: parseInt(e.target.value) || 1000 }))}
                            className="input"
                            style={{ width: '100%' }}
                          />
                        </div>
                        <div>
                          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                            Max Tokens (tokens)
                          </label>
                          <input
                            type="number"
                            min="256"
                            value={createModelForm.max_tokens}
                            onChange={(e) => setCreateModelForm(prev => ({ ...prev, max_tokens: parseInt(e.target.value) || 256 }))}
                            className="input"
                            style={{ width: '100%' }}
                          />
                        </div>
                      </div>

                      {/* Streaming SSE Checkbox */}
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        <input
                          type="checkbox"
                          checked={createModelForm.supports_streaming}
                          onChange={(e) => setCreateModelForm(prev => ({ ...prev, supports_streaming: e.target.checked }))}
                        />
                        <span>Supports real-time streaming (SSE)</span>
                      </label>
                    </div>

                    {/* Actions */}
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                      <button
                        type="button"
                        onClick={() => setShowCreateModal(false)}
                        className="btn btn-secondary"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={creatingModel}
                        className="btn btn-primary"
                      >
                        {creatingModel ? 'Saving...' : 'Save Model'}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {/* ============================================================ */}
            {/* MODAL 2: EDIT MODEL (FR-036, OP-023)                         */}
            {/* ============================================================ */}
            {editingModel && (
              <div style={{
                position: 'fixed',
                inset: 0,
                background: 'rgba(0, 0, 0, 0.75)',
                backdropFilter: 'blur(8px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000,
                padding: '1rem'
              }}>
                <div className="card" style={{
                  maxWidth: '500px',
                  width: '100%',
                  padding: '1.75rem'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      Edit Model Configuration (FR-036)
                    </h3>
                    <button
                      type="button"
                      onClick={() => setEditingModel(null)}
                      style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                    >
                      <Icon name="close" size={16} />
                    </button>
                  </div>

                  <form onSubmit={handleUpdateModel}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
                      {/* Immutable ID & Provider Info */}
                      <div style={{
                        padding: '10px 14px',
                        background: 'var(--bg-base)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.8rem',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}>
                        <div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>Model ID:</div>
                          <div style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--text-primary)' }}>{editingModel.id}</div>
                        </div>
                        <div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>Provider:</div>
                          <div style={{ fontWeight: 600, color: 'var(--accent)' }}>{editingModel.provider.toUpperCase()}</div>
                        </div>
                        <span className="badge" style={{ fontSize: '0.7rem' }}>
                          Immutable (BR-022)
                        </span>
                      </div>

                      {/* Display Name */}
                      <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                          Display Name *
                        </label>
                        <input
                          type="text"
                          required
                          value={editModelForm.name}
                          onChange={(e) => setEditModelForm(prev => ({ ...prev, name: e.target.value }))}
                          className="input"
                          style={{ width: '100%' }}
                        />
                      </div>

                      {/* Specs: Context & Max Tokens 2 Columns */}
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                        <div>
                          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                            Context Window (tokens)
                          </label>
                          <input
                            type="number"
                            min="1000"
                            value={editModelForm.context_window}
                            onChange={(e) => setEditModelForm(prev => ({ ...prev, context_window: parseInt(e.target.value) || 1000 }))}
                            className="input"
                            style={{ width: '100%' }}
                          />
                        </div>
                        <div>
                          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                            Max Tokens (tokens)
                          </label>
                          <input
                            type="number"
                            min="256"
                            value={editModelForm.max_tokens}
                            onChange={(e) => setEditModelForm(prev => ({ ...prev, max_tokens: parseInt(e.target.value) || 256 }))}
                            className="input"
                            style={{ width: '100%' }}
                          />
                        </div>
                      </div>

                      {/* Streaming SSE Checkbox */}
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        <input
                          type="checkbox"
                          checked={editModelForm.supports_streaming}
                          onChange={(e) => setEditModelForm(prev => ({ ...prev, supports_streaming: e.target.checked }))}
                        />
                        <span>Supports real-time streaming (SSE)</span>
                      </label>
                    </div>

                    {/* Actions */}
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                      <button
                        type="button"
                        onClick={() => setEditingModel(null)}
                        className="btn btn-secondary"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={updatingModel}
                        className="btn btn-primary"
                      >
                        {updatingModel ? 'Updating...' : 'Update Configuration'}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {/* ============================================================ */}
            {/* MODAL 3: CONFIRM SOFT ARCHIVE (FR-039, BR-023)              */}
            {/* ============================================================ */}
            {confirmArchiveModel && (
              <div style={{
                position: 'fixed',
                inset: 0,
                background: 'rgba(0, 0, 0, 0.75)',
                backdropFilter: 'blur(8px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000,
                padding: '1rem'
              }}>
                <div className="card" style={{
                  maxWidth: '460px',
                  width: '100%',
                  padding: '1.75rem',
                  border: '1px solid rgba(239, 68, 68, 0.35)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
                    <Icon name="trash" size={20} style={{ color: '#ef4444' }} />
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      Confirm Soft Archive (FR-039)
                    </h3>
                  </div>

                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '1.25rem' }}>
                    Are you sure you want to transition model <strong style={{ color: 'var(--text-primary)' }}>{confirmArchiveModel.name}</strong> (<code>{confirmArchiveModel.id}</code>) to <strong>ARCHIVED</strong> status?
                  </p>

                  <div style={{
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(239, 68, 68, 0.08)',
                    border: '1px solid rgba(239, 68, 68, 0.25)',
                    fontSize: '0.78rem',
                    color: '#fca5a5',
                    lineHeight: 1.5,
                    marginBottom: '1.5rem'
                  }}>
                    <strong>Data Preservation (BR-012):</strong> This is a soft archive operation. The model will be hidden from conversation pickers, but all historical messages and telemetry logs remain intact. You can restore it at any time.
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                    <button
                      type="button"
                      onClick={() => setConfirmArchiveModel(null)}
                      className="btn btn-secondary"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={() => handleArchiveModel(confirmArchiveModel)}
                      disabled={archivingModelId === confirmArchiveModel.id}
                      className="btn btn-danger"
                    >
                      {archivingModelId === confirmArchiveModel.id ? 'Archiving...' : 'Confirm Archive'}
                    </button>
                  </div>
                </div>
              </div>
            )}

          </div>
        )}

        {/* ============================================================ */}
        {/* TAB 6: API KEYS & INTEGRATIONS                                */}
        {/* ============================================================ */}
        {activeTab === 'api-keys' && (
          <ApiKeysTab showToast={showToast} userEmail={user?.email} />
        )}

        
      </div>
    </div>
  );
}
