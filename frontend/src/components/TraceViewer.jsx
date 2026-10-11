import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Terminal, Cpu } from 'lucide-react';

export function TraceViewer({ trace }) {
  const [expanded, setExpanded] = useState(false);

  if (!trace || trace.length === 0) return null;

  return (
    <div className="trace-container">
      <button
        className="trace-toggle"
        onClick={() => setExpanded(!expanded)}
        type="button"
        aria-expanded={expanded}
      >
        <div className="trace-toggle-left">
          <Terminal size={14} style={{ color: 'var(--emerald-primary)' }} />
          <span>Agent Reasoning & MCP Tool Execution</span>
          <span className="trace-badge">
            {trace.length} {trace.length === 1 ? 'step' : 'steps'}
          </span>
        </div>
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>

      {expanded && (
        <div className="trace-content">
          {trace.map((step, idx) => (
            <div key={idx} className="trace-step">
              <div className="trace-header" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Cpu size={12} color="var(--emerald-primary)" />
                <span className="trace-tool-title">
                  {step.tool ? `${step.tool}(${Object.keys(step.args || {}).join(', ')})` : 'Agent Reasoning'}
                </span>
              </div>

              {step.thought && (
                <div className="trace-thought" style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                  💭 {step.thought}
                </div>
              )}

              {step.args && Object.keys(step.args).length > 0 && (
                <div className="trace-detail-box">
                  <strong>Input:</strong> {JSON.stringify(step.args, null, 2)}
                </div>
              )}

              {step.result && (
                <div className="trace-detail-box">
                  <strong>Output:</strong>{' '}
                  {typeof step.result === 'object' && step.result !== null
                    ? JSON.stringify(step.result, null, 2)
                    : step.result}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
