/**
 * IndustrySelector — Initial screen to select industry and equipment model.
 * Premium glassmorphism design with animated cards.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Sun,
  Radio,
  Thermometer,
  FlaskConical,
  Factory,
  ChevronRight,
  Wrench,
} from "lucide-react";
import type { Industry, IndustryConfig } from "../types";

interface Props {
  onSelect: (industry: Industry, equipmentModel: string) => void;
}

const industries: IndustryConfig[] = [
  { id: "solar", label: "Solar", equipment: ["SMA-Sunny5000", "Fronius-Symo", "Huawei-SUN2000"] },
  { id: "telecom", label: "Telecom", equipment: ["Cisco-ASR9000", "Nokia-FSED", "Ericsson-RBS"] },
  { id: "hvac", label: "HVAC", equipment: ["Carrier-30XA", "Daikin-VRV", "Trane-CGAM"] },
  { id: "lab", label: "Lab Equipment", equipment: ["Agilent-HPLC", "Thermo-Centrifuge", "Beckman-UV"] },
  { id: "factory", label: "Factory", equipment: ["Siemens-S7-1500", "ABB-IRB6700", "Fanuc-R2000"] },
];

const industryIcons: Record<Industry, React.ElementType> = {
  solar: Sun,
  telecom: Radio,
  hvac: Thermometer,
  lab: FlaskConical,
  factory: Factory,
};

const industryGradients: Record<Industry, string> = {
  solar: "from-amber-500 to-orange-600",
  telecom: "from-blue-500 to-indigo-600",
  hvac: "from-cyan-500 to-teal-600",
  lab: "from-purple-500 to-pink-600",
  factory: "from-emerald-500 to-green-600",
};

export function IndustrySelector({ onSelect }: Props) {
  const [selectedIndustry, setSelectedIndustry] = useState<IndustryConfig | null>(null);

  return (
    <div className="min-h-full flex items-center justify-center p-6">
      <div className="max-w-2xl w-full">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl gradient-primary flex items-center justify-center">
              <Wrench className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gradient">FieldFix AI</h1>
          </div>
          <p className="text-text-secondary text-sm max-w-md mx-auto">
            Select your industry and equipment to begin. Point your camera at the
            device and describe the issue.
          </p>
        </motion.div>

        {!selectedIndustry ? (
          /* Industry Selection */
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {industries.map((industry, i) => {
              const Icon = industryIcons[industry.id];
              return (
                <motion.button
                  key={industry.id}
                  id={`industry-${industry.id}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  whileHover={{ scale: 1.03, y: -4 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => setSelectedIndustry(industry)}
                  className="glass rounded-2xl p-5 text-center group cursor-pointer border border-white/5 hover:border-primary/30 transition-colors"
                >
                  <div
                    className={`w-14 h-14 rounded-xl bg-gradient-to-br ${industryGradients[industry.id]} flex items-center justify-center mx-auto mb-3 group-hover:shadow-lg transition-shadow`}
                  >
                    <Icon className="w-7 h-7 text-white" />
                  </div>
                  <p className="text-sm font-semibold text-text-primary">
                    {industry.label}
                  </p>
                  <p className="text-xs text-text-muted mt-1">
                    {industry.equipment.length} models
                  </p>
                </motion.button>
              );
            })}
          </div>
        ) : (
          /* Equipment Selection */
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <button
              onClick={() => setSelectedIndustry(null)}
              className="text-sm text-text-muted hover:text-text-secondary mb-4 flex items-center gap-1 transition-colors"
            >
              ← Back to industries
            </button>

            <h2 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
              {(() => {
                const Icon = industryIcons[selectedIndustry.id];
                return <Icon className="w-5 h-5 text-primary-light" />;
              })()}
              {selectedIndustry.label} — Select Equipment
            </h2>

            <div className="space-y-2">
              {selectedIndustry.equipment.map((model, i) => (
                <motion.button
                  key={model}
                  id={`equipment-${model}`}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  whileHover={{ x: 4 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => onSelect(selectedIndustry.id, model)}
                  className="w-full glass rounded-xl p-4 flex items-center justify-between group cursor-pointer border border-white/5 hover:border-primary/30 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-surface-lighter flex items-center justify-center">
                      <Wrench className="w-5 h-5 text-text-secondary group-hover:text-primary-light transition-colors" />
                    </div>
                    <span className="text-sm font-medium text-text-primary">
                      {model}
                    </span>
                  </div>
                  <ChevronRight className="w-5 h-5 text-text-muted group-hover:text-primary-light transition-colors" />
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
