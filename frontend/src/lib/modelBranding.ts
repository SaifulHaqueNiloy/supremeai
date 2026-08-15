// বাংলা মন্তব্য: বাহিরের AI প্রোভাইডার (GPT/Claude/Gemini) এর র বদলে SupremeAI ব্র্যান্ডেড নাম দেখানোর জন্য সেন্ট্রাল ম্যাপিং ইউটিলিটি।

export interface SupremeModelInfo {
  label: string;
  family: 'core' | 'reason' | 'vision' | 'deep' | 'spark' | 'llama' | 'mistral' | 'generic';
}

const MODEL_MAP: Record<string, SupremeModelInfo> = {
  // OpenAI
  'gpt-4': { label: 'SupremeAI Core', family: 'core' },
  'gpt-4o': { label: 'SupremeAI Core', family: 'core' },
  'gpt-4o-mini': { label: 'SupremeAI Core Mini', family: 'core' },
  'gpt-4-turbo': { label: 'SupremeAI Core Turbo', family: 'core' },
  'gpt-3.5-turbo': { label: 'SupremeAI Spark', family: 'spark' },
  // Anthropic
  'claude-3-5-sonnet': { label: 'SupremeAI Reason', family: 'reason' },
  'claude-3-5-haiku': { label: 'SupremeAI Spark', family: 'spark' },
  'claude-3-opus': { label: 'SupremeAI Reason Pro', family: 'reason' },
  'claude-3': { label: 'SupremeAI Reason', family: 'reason' },
  // Google
  'gemini-1.5-pro': { label: 'SupremeAI Vision', family: 'vision' },
  'gemini-1.5-flash': { label: 'SupremeAI Vision Flash', family: 'vision' },
  'gemini-pro': { label: 'SupremeAI Vision', family: 'vision' },
  'gemini': { label: 'SupremeAI Vision', family: 'vision' },
  // DeepSeek
  'deepseek-chat': { label: 'SupremeAI Deep', family: 'deep' },
  'deepseek-coder': { label: 'SupremeAI Deep Coder', family: 'deep' },
  // Meta / Groq
  'llama3-70b-groq': { label: 'SupremeAI Llama', family: 'llama' },
  'llama': { label: 'SupremeAI Llama', family: 'llama' },
  // Mistral
  'mistral': { label: 'SupremeAI Mistral', family: 'mistral' },
};

const normalize = (raw: string): string =>
  raw?.trim().toLowerCase() ?? '';

export function getSupremeModelInfo(raw: string | undefined | null): SupremeModelInfo {
  if (!raw) return { label: 'SupremeAI Core', family: 'generic' };
  const key = normalize(raw);
  if (MODEL_MAP[key]) return MODEL_MAP[key];

  // ফলব্যাক: আংশিক মিল (যেমন gpt-4o-2024-...) খোঁজা
  const partial = Object.keys(MODEL_MAP).find((k) => key.startsWith(k) || k.startsWith(key));
  if (partial) return MODEL_MAP[partial];

  return { label: 'SupremeAI Core', family: 'generic' };
}

export function getSupremeModelLabel(raw: string | undefined | null): string {
  return getSupremeModelInfo(raw).label;
}
