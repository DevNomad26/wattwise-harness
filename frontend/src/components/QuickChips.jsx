import React from 'react';
import { SearchCheck, FileText, Sun, HelpCircle, Lightbulb } from 'lucide-react';

const SUGGESTIONS = [
  {
    icon: SearchCheck,
    label: 'Is my bill correct?',
    prompt: 'Check whether my electricity bill is calculated correctly according to the tariff rates.',
  },
  {
    icon: HelpCircle,
    label: 'Explain bill charges',
    prompt: 'Please explain each line item, tariff slab, and surcharge on my electricity bill in simple terms.',
  },
  {
    icon: Sun,
    label: 'Solar ROI estimate',
    prompt: 'Based on my monthly units consumption, estimate solar rooftop ROI, required capacity, and payback period.',
  },
  {
    icon: FileText,
    label: 'Draft complaint letter',
    prompt: 'Draft a formal complaint letter to the electricity board addressing the overcharge and discrepancies on my bill.',
  },
  {
    icon: Lightbulb,
    label: 'Energy saving tips',
    prompt: 'Give me practical recommendations to reduce my peak electricity consumption and lower my bill.',
  },
];

export function QuickChips({ onSelectPrompt, disabled }) {
  return (
    <div className="quick-chips-wrapper">
      {SUGGESTIONS.map((item, idx) => {
        const Icon = item.icon;
        return (
          <button
            key={idx}
            className="quick-chip"
            onClick={() => onSelectPrompt(item.prompt)}
            disabled={disabled}
            title={item.prompt}
          >
            <Icon size={14} />
            <span>{item.label}</span>
          </button>
        );
      })}
    </div>
  );
}
