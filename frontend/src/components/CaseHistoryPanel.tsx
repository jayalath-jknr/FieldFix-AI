/**
 * CaseHistoryPanel — shows previously resolved cases from Firestore.
 * Slides in from the right when cases are available.
 */

import { motion, AnimatePresence } from "framer-motion";
import { History, ChevronRight, Users, CheckCircle } from "lucide-react";
import type { HistoricalCase } from "../types";

interface Props {
  cases: HistoricalCase[];
  isOpen: boolean;
  onToggle: () => void;
}

export function CaseHistoryPanel({ cases, isOpen, onToggle }: Props) {
  return (
    <>
      {/* Toggle Button */}
      <button
        id="case-history-toggle"
        onClick={onToggle}
        className={`
          fixed right-0 top-1/2 -translate-y-1/2 z-40
          glass rounded-l-xl px-2 py-4
          transition-all duration-300 hover:bg-surface-lighter
          ${isOpen ? "right-80" : "right-0"}
        `}
      >
        <History className="w-5 h-5 text-text-secondary" />
        {cases.length > 0 && (
          <span className="absolute -top-1 -left-1 w-5 h-5 bg-primary rounded-full text-[10px] font-bold flex items-center justify-center text-white">
            {cases.length}
          </span>
        )}
      </button>

      {/* Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: 320 }}
            animate={{ x: 0 }}
            exit={{ x: 320 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 bottom-0 w-80 z-30 glass border-l border-white/5 overflow-y-auto"
          >
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                  <History className="w-4 h-4 text-primary-light" />
                  Case History
                </h3>
                <button
                  onClick={onToggle}
                  className="text-text-muted hover:text-text-secondary transition-colors"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>

              {cases.length === 0 ? (
                <p className="text-sm text-text-muted text-center py-8">
                  No previous cases found for this equipment.
                </p>
              ) : (
                <div className="space-y-3">
                  {cases.map((c, i) => (
                    <motion.div
                      key={c.case_id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="glass-light rounded-xl p-3 border border-white/5"
                    >
                      <div className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-success mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-text-primary line-clamp-2">
                            {c.fault_summary}
                          </p>
                          <p className="text-xs text-text-secondary mt-1 line-clamp-2">
                            {c.resolution}
                          </p>

                          {c.steps_taken.length > 0 && (
                            <div className="mt-2 space-y-1">
                              {c.steps_taken.slice(0, 3).map((step, j) => (
                                <p
                                  key={j}
                                  className="text-xs text-text-muted flex items-start gap-1"
                                >
                                  <span className="text-primary-light mt-px">
                                    {j + 1}.
                                  </span>
                                  <span className="line-clamp-1">{step}</span>
                                </p>
                              ))}
                              {c.steps_taken.length > 3 && (
                                <p className="text-xs text-text-muted">
                                  +{c.steps_taken.length - 3} more steps
                                </p>
                              )}
                            </div>
                          )}

                          <div className="flex items-center gap-3 mt-2 pt-2 border-t border-white/5">
                            <span className="text-[10px] text-text-muted flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {c.technician_count}{" "}
                              {c.technician_count === 1
                                ? "technician"
                                : "technicians"}
                            </span>
                            <span className="text-[10px] text-text-muted">
                              {c.resolved_date}
                            </span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
