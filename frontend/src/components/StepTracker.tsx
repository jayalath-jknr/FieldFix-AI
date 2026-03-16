/**
 * StepTracker — shows the current repair step and progress through
 * the resolution process. Steps are added as the agent guides.
 */

import { motion } from "framer-motion";
import { Check, Circle, ArrowRight } from "lucide-react";
import type { RepairStep } from "../types";

interface Props {
  steps: RepairStep[];
}

export function StepTracker({ steps }: Props) {
  if (steps.length === 0) return null;

  const completedCount = steps.filter((s) => s.confirmed).length;

  return (
    <div className="glass rounded-xl p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
          Repair Progress
        </h3>
        <span className="text-xs text-text-muted">
          {completedCount}/{steps.length} steps
        </span>
      </div>

      {/* Progress Bar */}
      <div className="h-1 bg-surface-lighter rounded-full mb-4 overflow-hidden">
        <motion.div
          className="h-full gradient-primary rounded-full"
          initial={{ width: 0 }}
          animate={{
            width: `${steps.length > 0 ? (completedCount / steps.length) * 100 : 0}%`,
          }}
          transition={{ duration: 0.5 }}
        />
      </div>

      {/* Steps */}
      <div className="space-y-2.5">
        {steps.map((step, i) => {
          const isActive =
            !step.confirmed &&
            (i === 0 || steps[i - 1]?.confirmed);

          return (
            <motion.div
              key={step.index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className={`flex items-start gap-2.5 ${
                step.confirmed
                  ? "opacity-60"
                  : isActive
                  ? ""
                  : "opacity-40"
              }`}
            >
              <div className="mt-0.5 flex-shrink-0">
                {step.confirmed ? (
                  <div className="w-5 h-5 rounded-full bg-success/20 flex items-center justify-center">
                    <Check className="w-3 h-3 text-success" />
                  </div>
                ) : isActive ? (
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                    className="w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center"
                  >
                    <ArrowRight className="w-3 h-3 text-primary-light" />
                  </motion.div>
                ) : (
                  <div className="w-5 h-5 rounded-full bg-surface-lighter flex items-center justify-center">
                    <Circle className="w-3 h-3 text-text-muted" />
                  </div>
                )}
              </div>
              <p
                className={`text-sm ${
                  isActive
                    ? "text-text-primary font-medium"
                    : "text-text-secondary"
                }`}
              >
                {step.instruction}
              </p>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
