export type ToolEvent = {
  id: string;
  name: string;
  status: "running" | "completed" | "failed";
  input: Record<string, unknown>;
  output: string;
};

export type Message = {
  id: string;
  chat_id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  tool_events: ToolEvent[];
  attachments: { file_id: string; name: string }[];
  created_at: string;
};

export type ChatSummary = {
  id: string;
  title: string;
  model: string;
  system_prompt?: string | null;
  pinned: boolean;
  created_at: string;
  updated_at: string;
  last_message: string;
};

export type ChatDetail = ChatSummary & {
  messages: Message[];
};

export type ModelInfo = {
  name: string;
  size?: number;
  modified_at?: string;
};
