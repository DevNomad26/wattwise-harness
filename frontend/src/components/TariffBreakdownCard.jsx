import React, { useMemo } from 'react';
import { CheckCircle2, AlertTriangle, ShieldAlert, Zap, Layers } from 'lucide-react';

const STATE_SLABS = {
  maharashtra: [
    { upto: 100, rate: 5.56, label: '0–100 kWh' },
    { upto: 300, rate: 12.40, label: '101–300 kWh' },
    { upto: 500, rate: 16.64, label: '301–500 kWh' },
    { upto: null, rate: 19.13, label: '>500 kWh' },
  ],
  gujarat: [
    { upto: 50, rate: 3.05, label: '0–50 kWh' },
    { upto: 100, rate: 3.50, label: '51–100 kWh' },
    { upto: 250, rate: 4.15, label: '101–250 kWh' },
    { upto: null, rate: 5.20, label: '>250 kWh' },
  ],
  rajasthan: [
    { upto: 50, rate: 4.75, label: '0–50 kWh' },
    { upto: 150, rate: 6.50, label: '51–150 kWh' },
    { upto: 300, rate: 7.35, label: '151–300 kWh' },
    { upto: 500, rate: 7.65, label: '301–500 kWh' },
    { upto: null, rate: 7.95, label: '>500 kWh' },
  ],
  delhi: [
    { upto: 200, rate: 3.00, label: '0–200 kWh' },
    { upto: 400, rate: 4.50, label: '201–400 kWh' },
    { upto: 800, rate: 6.50, label: '401–800 kWh' },
    { upto: 1200, rate: 7.00, label: '801–1200 kWh' },
    { upto: null, rate: 8.00, label: '>1200 kWh' },
  ],
  karnataka: [
    { upto: null, rate: 5.80, label: 'All Units' },
  ],
};

const SLAB_COLORS = [
  'var(--emerald-primary)',
  '#06b6d4', // Cyan
  '#8b5cf6', // Violet
  '#f59e0b', // Amber
  '#ef4444', // Rose
];

export function TariffBreakdownCard({ message }) {
  const auditData = useMemo(() => {
    if (!message || message.role !== 'assistant') return null;

    const trace = message.trace || [];
    let units = null;
    let state = null;
    let computedTotal = null;
    let fixedCharges = null;
    let energyCharges = null;
    let dutyCharges = null;
    let billedAmount = null;
    let discom = null;

    // 1. Inspect compute_bill step
    for (const step of trace) {
      if (step.tool === 'compute_bill' && step.result) {
        if (step.args) {
          units = step.args.units ? parseFloat(step.args.units) : units;
          state = step.args.state || state;
        }

        // Match result: "Total bill for 250.0 units in Maharashtra is Rs 2932.56 (Includes Rs 130.00 fixed, Rs 2416.00 energy, Rs 386.56 duty)."
        const rx = /Total bill for ([\d.]+) units in ([\w\s]+) is Rs ([\d.]+) \(Includes Rs ([\d.]+) fixed, Rs ([\d.]+) energy, Rs ([\d.]+) duty\)/i;
        const match = step.result.match(rx);
        if (match) {
          units = parseFloat(match[1]);
          state = match[2].trim();
          computedTotal = parseFloat(match[3]);
          fixedCharges = parseFloat(match[4]);
          energyCharges = parseFloat(match[5]);
          dutyCharges = parseFloat(match[6]);
        }
      }

      // 2. Inspect extract_bill_data step
      if (step.tool === 'extract_bill_data' && step.result) {
        try {
          const parsed = typeof step.result === 'string' ? JSON.parse(step.result) : step.result;
          if (parsed && typeof parsed === 'object') {
            if (parsed.units && units === null) units = parseFloat(parsed.units);
            if (parsed.state && !state) state = parsed.state;
            if (parsed.discom) discom = parsed.discom;
            if (parsed.total_amount_due !== undefined && parsed.total_amount_due !== null) {
              billedAmount = parseFloat(parsed.total_amount_due);
            }
          }
        } catch {}
      }
    }

    // If no compute_bill in trace, attempt fallback regex on assistant text
    if (computedTotal === null && message.content) {
      const rxText = /Total bill for ([\d.]+) units in ([\w\s]+) is Rs ([\d.]+) \(Includes Rs ([\d.]+) fixed, Rs ([\d.]+) energy, Rs ([\d.]+) duty\)/i;
      const matchText = message.content.match(rxText);
      if (matchText) {
        units = parseFloat(matchText[1]);
        state = matchText[2].trim();
        computedTotal = parseFloat(matchText[3]);
        fixedCharges = parseFloat(matchText[4]);
        energyCharges = parseFloat(matchText[5]);
        dutyCharges = parseFloat(matchText[6]);
      }
    }

    if (computedTotal === null || units === null) {
      return null;
    }

    // Calculate slab breakdown
    const stateKey = (state || '').toLowerCase();
    const slabs = STATE_SLABS[stateKey] || [];
    const slabSegments = [];

    if (slabs.length > 0 && units > 0) {
      let remaining = units;
      let prevLimit = 0;

      for (let i = 0; i < slabs.length; i++) {
        const slab = slabs[i];
        if (remaining <= 0) break;

        let blockUnits = 0;
        if (slab.upto === null) {
          blockUnits = remaining;
          remaining = 0;
        } else {
          const blockSize = slab.upto - prevLimit;
          blockUnits = Math.min(remaining, blockSize);
          remaining -= blockUnits;
          prevLimit = slab.upto;
        }

        if (blockUnits > 0) {
          const slabCost = blockUnits * slab.rate;
          const percentage = (blockUnits / units) * 100;
          slabSegments.push({
            label: slab.label,
            units: blockUnits,
            rate: slab.rate,
            cost: slabCost,
            percentage,
            color: SLAB_COLORS[i % SLAB_COLORS.length],
          });
        }
      }
    }

    // Discrepancy analysis
    let discrepancy = null;
    if (billedAmount !== null && !isNaN(billedAmount)) {
      discrepancy = billedAmount - computedTotal;
    }

    return {
      units,
      state: state || 'Domestic',
      discom: discom || (state ? `${state} Electricity Board` : 'DISCOM'),
      computedTotal,
      fixedCharges: fixedCharges || 0,
      energyCharges: energyCharges || 0,
      dutyCharges: dutyCharges || 0,
      billedAmount,
      discrepancy,
      slabSegments,
    };
  }, [message]);

  if (!auditData) return null;

  const {
    units,
    state,
    discom,
    computedTotal,
    fixedCharges,
    energyCharges,
    dutyCharges,
    billedAmount,
    discrepancy,
    slabSegments,
  } = auditData;

  const isMatched = discrepancy !== null && Math.abs(discrepancy) <= 5;
  const isOvercharged = discrepancy !== null && discrepancy > 5;
  const isUndercharged = discrepancy !== null && discrepancy < -5;

  return (
    <div className="tariff-card">
      {/* Header */}
      <div className="tariff-card-header">
        <div className="tariff-card-title-group">
          <div className="tariff-icon-badge">
            <Zap size={14} />
          </div>
          <div>
            <h4 className="tariff-card-title">Verified Tariff Audit Breakdown</h4>
            <p className="tariff-card-subtitle">{discom}</p>
          </div>
        </div>

        <div className="tariff-pills-group">
          <span className="tariff-pill state-pill">{state}</span>
          <span className="tariff-pill units-pill">{units} kWh</span>
        </div>
      </div>

      {/* Visual Multi-Slab Consumption Segment Bar */}
      {slabSegments.length > 0 && (
        <div className="slab-visualizer-container">
          <div className="slab-visualizer-label">
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
              <Layers size={12} /> Consumption Slab Allocation
            </span>
            <span>{units} Total Billed Units</span>
          </div>

          <div className="slab-bar-track">
            {slabSegments.map((seg, idx) => (
              <div
                key={idx}
                className="slab-bar-segment"
                style={{
                  width: `${seg.percentage}%`,
                  backgroundColor: seg.color,
                }}
                title={`${seg.label}: ${seg.units.toFixed(1)} units @ ₹${seg.rate.toFixed(2)} = ₹${seg.cost.toFixed(2)}`}
              />
            ))}
          </div>

          {/* Slab Legend Chips */}
          <div className="slab-legend-grid">
            {slabSegments.map((seg, idx) => (
              <div key={idx} className="slab-legend-item">
                <span className="slab-legend-dot" style={{ backgroundColor: seg.color }} />
                <span className="slab-legend-name">{seg.label}:</span>
                <span className="slab-legend-calc">
                  {seg.units}u × ₹{seg.rate} = <strong>₹{seg.cost.toFixed(2)}</strong>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4 Financial Metrics Grid */}
      <div className="tariff-metrics-grid">
        <div className="tariff-metric-box">
          <span className="metric-label">Energy Slabs</span>
          <span className="metric-value">₹{energyCharges.toFixed(2)}</span>
        </div>
        <div className="tariff-metric-box">
          <span className="metric-label">Fixed Monthly</span>
          <span className="metric-value">₹{fixedCharges.toFixed(2)}</span>
        </div>
        <div className="tariff-metric-box">
          <span className="metric-label">Electricity Duty</span>
          <span className="metric-value">₹{dutyCharges.toFixed(2)}</span>
        </div>
        <div className="tariff-metric-box total-box">
          <span className="metric-label">Official Tariff Total</span>
          <span className="metric-value highlight">₹{computedTotal.toFixed(2)}</span>
        </div>
      </div>

      {/* Discrepancy & Verification Verdict Badge */}
      {discrepancy !== null && (
        <div
          className={`tariff-verdict-banner ${
            isMatched ? 'verified' : isOvercharged ? 'overcharged' : 'undercharged'
          }`}
        >
          {isMatched && (
            <>
              <CheckCircle2 size={16} />
              <div>
                <strong>Bill Matches Official Tariff</strong>
                <p>Billed ₹{billedAmount?.toFixed(2)} matches verified formula within ₹5 margin.</p>
              </div>
            </>
          )}

          {isOvercharged && (
            <>
              <ShieldAlert size={16} />
              <div>
                <strong>Potential Overcharge Detected: ₹{discrepancy.toFixed(2)}</strong>
                <p>
                  Billed ₹{billedAmount?.toFixed(2)} exceeds verified tariff amount of ₹{computedTotal.toFixed(2)}. Check for meter mistakes or late fees.
                </p>
              </div>
            </>
          )}

          {isUndercharged && (
            <>
              <AlertTriangle size={16} />
              <div>
                <strong>Lower Than Standard Tariff: ₹{Math.abs(discrepancy).toFixed(2)}</strong>
                <p>
                  Billed ₹{billedAmount?.toFixed(2)} vs standard ₹{computedTotal.toFixed(2)}. Connection may have domestic government subsidies or solar credits applied.
                </p>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
