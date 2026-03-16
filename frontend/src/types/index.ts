export type Industry = "solar" | "telecom" | "hvac" | "lab" | "factory";
export type AgentState = "idle" | "listening" | "thinking" | "speaking" | "interrupted";
export type Severity = "low" | "medium" | "high" | "critical" | "unknown";

export interface Citation {
  source: string;
  section: string;
  page: number;
  citation: string;  // formatted: "Manual Name §4.3 · p.44"
  text: string;      // relevant excerpt
}

export interface Diagnosis {
  likely_fault: string;
  severity: Severity;
  confidence: number;
  draw_attention_to: string;
  immediate_action: string;
  parts_likely_needed: string[];
  safe_to_operate: boolean;
  needs_closer_view: boolean;
  closer_view_instruction?: string;
}

export interface HistoricalCase {
  case_id: string;
  fault_summary: string;
  resolution: string;
  steps_taken: string[];
  resolved_date: string;
  technician_count: number;
}

export interface RepairStep {
  index: number;
  instruction: string;
  confirmed: boolean;
  timestamp: Date;
}

export interface SessionState {
  sessionId: string | null;
  industry: Industry | null;
  equipmentModel: string | null;
  agentState: AgentState;
  currentDiagnosis: Diagnosis | null;
  citations: Citation[];
  repairSteps: RepairStep[];
  historicalCases: HistoricalCase[];
  isConnected: boolean;
  error: string | null;
}

export interface IndustryConfig {
  id: Industry;
  label: string;
  equipment: string[];
}

export interface ToolResultMessage {
  type: "tool_result";
  tool: string;
  data: Record<string, unknown>;
}

export interface SessionReadyMessage {
  type: "session_ready";
  session_id: string;
}

export type ServerMessage = ToolResultMessage | SessionReadyMessage;
