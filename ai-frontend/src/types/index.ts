export * from './rule';
export * from './apiKey';
import { AttachmentItem } from '@/services/attachmentService';
export type { AttachmentItem };

export type Role = 'user' | 'assistant' | 'system' | 'tool';

export interface Message {
  id: string;
  role: Role;
  content: string;
  timestamp: number;
  tokens?: number;
  model?: string;
  source?: 'WEB' | 'DISCORD';
  status?: 'pending' | 'streaming' | 'completed' | 'error';
  attachments?: AttachmentItem[];
}


export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

export interface LLMProviderOption {
  id: string;
  name: string;
  provider: 'openai' | 'gemini' | 'anthropic' | 'ollama';
  modelId: string;
}

export interface AgentModel {
  id: string;
  name: string;
  provider: 'google' | 'anthropic' | 'openai' | 'groq' | 'ollama';
  status: 'ACTIVE' | 'INACTIVE' | 'DEGRADED' | 'ARCHIVED';
  is_default: boolean;
  context_window: number;
  max_tokens: number;
  supports_streaming: boolean;
  has_api_key: boolean;
  latency_ms: number | null;
  last_checked_at: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ModelSearchResponse {
  total: number;
  execution_time_ms: number;
  items: AgentModel[];
}

export interface UserQuotaStatus {
  user_id: string;
  daily_token_limit: number;
  daily_tokens_used: number;
  percent_used: number;
  warning_80: boolean;
  reset_at: string;
}

export interface MetricTrendPoint {
  time: string;
  latency_ms: number;
  ttft_ms: number;
  tokens: number;
}

export interface ResourceSummary {
  time_range: '1h' | '24h' | '7d' | '30d';
  total_requests: number;
  avg_latency_ms: number;
  avg_ttft_ms: number;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  status_counts: {
    '2xx': number;
    '4xx': number;
    '5xx': number;
  };
  tokens_by_provider: {
    google: number;
    openai: number;
    anthropic: number;
    other: number;
  };
  recent_trend: MetricTrendPoint[];
  quota_status: UserQuotaStatus;
}

export interface ApiMetricLogItem {
  id: string;
  user_id: string | null;
  endpoint: string;
  method: string;
  status_code: number;
  latency_ms: number;
  ttft_ms: number | null;
  model_name: string | null;
  provider: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  error_code: string | null;
  created_at: string;
}

export interface SSEMetricEvent {
  metric: ApiMetricLogItem;
  quota: {
    daily_tokens_used: number;
    daily_token_limit: number;
    percent_used: number;
    warning_80: boolean;
  };
}


// ==============================================================================
// SYSTEM PROMPTS (SENSEI PROMPTS) TYPES
// ==============================================================================
export interface _LegacyPromptSummary {
  id: string;
  name: string;
  description: string | null;
  content_length: number;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface _LegacyPromptDetail extends SystemPromptSummary {
  content: string;
}

export interface _LegacyPromptListResponse {
  prompts: SystemPromptSummary[];
}

export interface SystemPromptCreateRequest {
  name: string;
  description?: string | null;
  content: string;
  age?: number;
  gender?: string;
  japanese_level?: string;
  personality?: string | null;
  teaching_style?: string | null;
  catchphrase?: string | null;
  hobbies?: string | null;
  avatar_url?: string | null;
  voice_id?: string | null;
  is_default?: boolean;
}

export interface SystemPromptUpdateRequest {
  name?: string;
  description?: string | null;
  content?: string;
  age?: number;
  gender?: string;
  japanese_level?: string;
  personality?: string | null;
  teaching_style?: string | null;
  catchphrase?: string | null;
  hobbies?: string | null;
  avatar_url?: string | null;
  voice_id?: string | null;
  is_default?: boolean;
}

export interface UserConnectionsResponse {
  has_password: boolean;
  connections: Record<string, any>;
}

export interface SystemPromptSummary {
  id: string;
  name: string;
  description: string | null;
  content_length: number;
  age?: number;
  gender?: string;
  japanese_level?: string;
  personality?: string | null;
  teaching_style?: string | null;
  catchphrase?: string | null;
  hobbies?: string | null;
  avatar_url?: string | null;
  voice_id?: string | null;
  is_default: boolean;
  is_system_preset?: boolean;
  created_at: string;
  updated_at: string;
}

export interface SystemPromptDetail extends SystemPromptSummary {
  content: string;
  attachments?: any[];
}

export interface SystemPromptListResponse {
  prompts?: SystemPromptSummary[];
  items?: SystemPromptSummary[];
  total?: number;
}

export type SenseiSummary = SystemPromptSummary;
export type SenseiDetail = SystemPromptDetail;
export type SenseiCreateRequest = SystemPromptCreateRequest;
export type SenseiUpdateRequest = SystemPromptUpdateRequest;

export interface VoiceItem {
  id: string;
  name: string;
  character_name: string;
  speaker_id: number;
  style_name?: string;
  gender: 'female' | 'male' | 'other' | string;
  description?: string | null;
  speed_scale: number;
  pitch_scale: number;
  intonation_scale: number;
  volume_scale: number;
  sample_text?: string | null;
  avatar_url?: string | null;
  status: 'ACTIVE' | 'INACTIVE' | string;
  is_system_preset?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface VoiceEngineStatus {
  engine_available: boolean;
  engine_url: string;
  version?: string | null;
  latency_ms?: number | null;
  cached_audio_count: number;
  error?: string | null;
}

export interface VoiceListResponse {
  total: number;
  items: VoiceItem[];
}

export interface VoiceSynthesizeRequest {
  text: string;
  speaker_id?: number;
  speed_scale?: number;
  pitch_scale?: number;
  intonation_scale?: number;
  volume_scale?: number;
}
