import React from 'react';
import { AlertTriangle, CheckCircle2, Info, Compass, ShieldAlert, Award } from 'lucide-react';

export const CorrectionCard = ({ correction }) => {
  if (!correction) return null;

  const {
    title,
    severity,
    observed_difference,
    reference_benchmark,
    location_and_timing,
    suggested_correction,
    evidence_and_confidence,
    efficiency_impact,
    injury_caution,
  } = correction;

  const severityColor =
    severity === 'high'
      ? 'border-rose-500/40 bg-rose-500/5'
      : severity === 'medium'
      ? 'border-amber-500/40 bg-amber-500/5'
      : 'border-blue-500/40 bg-blue-500/5';

  const badgeColor =
    severity === 'high'
      ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
      : severity === 'medium'
      ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
      : 'bg-blue-500/20 text-blue-300 border-blue-500/30';

  return (
    <div className={`rounded-2xl border p-5 transition shadow-lg ${severityColor} backdrop-blur-md`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <div className="flex items-center space-x-2.5">
          <AlertTriangle
            className={`w-5 h-5 ${
              severity === 'high' ? 'text-rose-400' : 'text-amber-400'
            }`}
          />
          <h3 className="font-bold text-slate-100 text-base">{title}</h3>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border uppercase ${badgeColor}`}>
            {severity} Priority
          </span>
          <span className="text-[11px] font-semibold text-slate-400 bg-slate-800/80 px-2.5 py-0.5 rounded-full border border-slate-700">
            {location_and_timing}
          </span>
        </div>
      </div>

      {/* 5-Element Pillars Grid */}
      <div className="space-y-3 mt-4 text-xs">
        {/* 1. Observed Difference */}
        <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
          <div className="flex items-center space-x-1.5 text-slate-400 font-semibold mb-1 uppercase tracking-wider text-[10px]">
            <Compass className="w-3.5 h-3.5 text-indigo-400" />
            <span>Observed Technique Deviation</span>
          </div>
          <p className="text-slate-200 font-medium">{observed_difference}</p>
        </div>

        {/* 2. Reference Benchmark */}
        <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
          <div className="flex items-center space-x-1.5 text-slate-400 font-semibold mb-1 uppercase tracking-wider text-[10px]">
            <Award className="w-3.5 h-3.5 text-cyan-400" />
            <span>Coach Reference Target</span>
          </div>
          <p className="text-cyan-200 font-medium">{reference_benchmark}</p>
        </div>

        {/* 3. Actionable Coaching Cue */}
        <div className="bg-emerald-950/30 p-3 rounded-xl border border-emerald-800/40">
          <div className="flex items-center space-x-1.5 text-emerald-400 font-semibold mb-1 uppercase tracking-wider text-[10px]">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Suggested Actionable Adjustment</span>
          </div>
          <p className="text-emerald-200 font-semibold text-sm leading-relaxed">{suggested_correction}</p>
        </div>

        {/* 4. Efficiency Impact */}
        {efficiency_impact && (
          <div className="bg-slate-900/50 p-3 rounded-xl border border-slate-800/60">
            <span className="text-slate-400 font-semibold block mb-0.5 uppercase tracking-wider text-[10px]">
              Kinetic Chain Efficiency Impact
            </span>
            <p className="text-slate-300">{efficiency_impact}</p>
          </div>
        )}

        {/* 5. Cautious Injury-Related Note */}
        {injury_caution && (
          <div className="bg-rose-950/20 p-3 rounded-xl border border-rose-900/30">
            <div className="flex items-center space-x-1.5 text-rose-400 font-semibold mb-1 uppercase tracking-wider text-[10px]">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
              <span>Biomechanical Joint Load Caution</span>
            </div>
            <p className="text-rose-200/90 text-[11px] leading-relaxed">{injury_caution}</p>
            <p className="text-[10px] text-rose-400/60 italic mt-1.5">
              * Educational observation based on sports biomechanics literature. Not medical diagnosis or injury prediction.
            </p>
          </div>
        )}

        {/* Confidence & Evidence Footer */}
        {evidence_and_confidence && (
          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-800/60">
            <span>Evidence: {evidence_and_confidence.evidence_level}</span>
            <span>
              Confidence Score:{' '}
              <strong className="text-slate-400">
                {Math.round((evidence_and_confidence.confidence_score || 0.8) * 100)}%
              </strong>
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default CorrectionCard;
