/**
 * CitationCard — appears below the camera feed when the agent
 * cites a manual section. Animates in from below.
 */

import { motion } from "framer-motion";
import { BookOpen } from "lucide-react";
import type { Citation } from "../types";

interface Props {
  citation: Citation;
  isLatest: boolean;
}

export function CitationCard({ citation, isLatest }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={`
        rounded-xl p-3.5 mb-2 transition-colors duration-200
        ${
          isLatest
            ? "glass border border-primary/30 shadow-lg shadow-primary/10"
            : "glass-light border border-white/5"
        }
      `}
    >
      <div className="flex items-start gap-2.5">
        <BookOpen
          className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
            isLatest ? "text-primary-light" : "text-text-muted"
          }`}
        />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-text-primary leading-relaxed line-clamp-3">
            {citation.text}
          </p>
          <div className="mt-2">
            <span
              className={`
                text-xs font-semibold px-2.5 py-1 rounded-full inline-block
                ${
                  isLatest
                    ? "bg-primary/20 text-primary-light"
                    : "bg-surface-lighter text-text-muted"
                }
              `}
            >
              {citation.citation}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
