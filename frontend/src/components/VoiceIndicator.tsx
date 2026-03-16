/**
 * VoiceIndicator — animated indicator showing the agent state:
 * idle, listening, thinking, speaking, interrupted.
 */

import { motion } from "framer-motion";
import {
  Mic,
  MicOff,
  Volume2,
  Brain,
  AlertCircle,
} from "lucide-react";
import type { AgentState } from "../types";

interface Props {
  state: AgentState;
}

const stateConfig: Record<
  AgentState,
  {
    icon: React.ElementType;
    label: string;
    color: string;
    bgColor: string;
    animate: boolean;
  }
> = {
  idle: {
    icon: MicOff,
    label: "Ready",
    color: "text-text-muted",
    bgColor: "bg-surface-lighter",
    animate: false,
  },
  listening: {
    icon: Mic,
    label: "Listening...",
    color: "text-green-400",
    bgColor: "bg-green-500/20",
    animate: true,
  },
  thinking: {
    icon: Brain,
    label: "Analyzing...",
    color: "text-amber-400",
    bgColor: "bg-amber-500/20",
    animate: true,
  },
  speaking: {
    icon: Volume2,
    label: "Speaking...",
    color: "text-primary-light",
    bgColor: "bg-primary/20",
    animate: true,
  },
  interrupted: {
    icon: AlertCircle,
    label: "Interrupted",
    color: "text-orange-400",
    bgColor: "bg-orange-500/20",
    animate: false,
  },
};

export function VoiceIndicator({ state }: Props) {
  const config = stateConfig[state];
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-3">
      {/* Animated Ring */}
      <div className="relative">
        {config.animate && (
          <>
            <motion.div
              className={`absolute inset-0 rounded-full ${config.bgColor}`}
              animate={{ scale: [1, 1.5, 1], opacity: [0.6, 0, 0.6] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <motion.div
              className={`absolute inset-0 rounded-full ${config.bgColor}`}
              animate={{ scale: [1, 1.3, 1], opacity: [0.4, 0, 0.4] }}
              transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
            />
          </>
        )}
        <div
          className={`relative w-10 h-10 rounded-full ${config.bgColor} flex items-center justify-center`}
        >
          <Icon className={`w-5 h-5 ${config.color}`} />
        </div>
      </div>

      {/* Label */}
      <div>
        <p className={`text-sm font-medium ${config.color}`}>
          {config.label}
        </p>
        {state === "listening" && (
          <div className="flex gap-1 mt-1">
            {[0, 1, 2, 3, 4].map((i) => (
              <motion.div
                key={i}
                className="w-1 bg-green-400 rounded-full"
                animate={{ height: [4, 12, 4] }}
                transition={{
                  duration: 0.6,
                  repeat: Infinity,
                  delay: i * 0.1,
                }}
              />
            ))}
          </div>
        )}
        {state === "speaking" && (
          <div className="flex gap-1 mt-1">
            {[0, 1, 2, 3, 4, 5, 6].map((i) => (
              <motion.div
                key={i}
                className="w-0.5 bg-primary-light rounded-full"
                animate={{ height: [3, 16, 3] }}
                transition={{
                  duration: 0.5,
                  repeat: Infinity,
                  delay: i * 0.07,
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
