/**
 * Zustand store for FieldFix AI session state.
 */

import { create } from "zustand";
import type {
  AgentState,
  Citation,
  Diagnosis,
  HistoricalCase,
  Industry,
  RepairStep,
} from "../types";

interface SessionStore {
  // State
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

  // Actions
  setSessionId: (id: string | null) => void;
  setIndustry: (industry: Industry | null) => void;
  setEquipmentModel: (model: string | null) => void;
  setAgentState: (state: AgentState) => void;
  setDiagnosis: (diagnosis: Diagnosis | null) => void;
  addCitation: (citation: Citation) => void;
  addRepairStep: (step: RepairStep) => void;
  confirmStep: (index: number) => void;
  addHistoricalCase: (c: HistoricalCase) => void;
  setConnected: (connected: boolean) => void;
  setError: (error: string | null) => void;
  resetSession: () => void;
}

const initialState = {
  sessionId: null,
  industry: null,
  equipmentModel: null,
  agentState: "idle" as AgentState,
  currentDiagnosis: null,
  citations: [],
  repairSteps: [],
  historicalCases: [],
  isConnected: false,
  error: null,
};

export const useSessionStore = create<SessionStore>((set) => ({
  ...initialState,

  setSessionId: (id) => set({ sessionId: id }),
  setIndustry: (industry) => set({ industry }),
  setEquipmentModel: (model) => set({ equipmentModel: model }),
  setAgentState: (agentState) => set({ agentState }),
  setDiagnosis: (diagnosis) => set({ currentDiagnosis: diagnosis }),

  addCitation: (citation) =>
    set((s) => ({
      citations: [...s.citations, citation],
    })),

  addRepairStep: (step) =>
    set((s) => ({
      repairSteps: [...s.repairSteps, step],
    })),

  confirmStep: (index) =>
    set((s) => ({
      repairSteps: s.repairSteps.map((step) =>
        step.index === index ? { ...step, confirmed: true } : step
      ),
    })),

  addHistoricalCase: (c) =>
    set((s) => ({
      historicalCases: [...s.historicalCases, c],
    })),

  setConnected: (connected) => set({ isConnected: connected }),
  setError: (error) => set({ error }),

  resetSession: () => set(initialState),
}));
