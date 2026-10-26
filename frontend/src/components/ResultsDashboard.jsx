import React from 'react';
import { BarChart3, Film, ListFilter, CheckCircle, AlertCircle, Award } from 'lucide-react';
import InteractivePlayer from './InteractivePlayer';
import CorrectionCard from './CorrectionCard';

export default function ResultsDashboard({ result, videoUrl }) {
  if (!result) return null;

  // Handle both V1 format (with phases, metrics, corrections) and legacy format
  const isV1 = !!result.corrections || !!result.phases;

  const phases = result.phases || {};
  const metrics = result.metrics || result.summary || {};
  const corrections = result.corrections || [];
  const reference = result.reference || {};
  const benchmarkMetrics = reference.benchmark_metrics || {};

  const sport = result.sport || 'badminton';
  const movement = result.movement || 'overhead_clear';

  // Resolve videoUrl if not provided directly or if loaded from past session
  const activeVideoUrl =
    videoUrl ||
    (result.job_id ? `/api/v1/analyses/${result.job_id}/video` : null) ||
    result.video_output_url ||
    (result.session_id ? `/api/outputs/${result.session_id}_annotated.mp4` : null);

  return (
    <div className="space-y-8">
      {/* 1. Synchronized Interactive Video Player */}
      <section>
        <InteractivePlayer
          videoUrl={activeVideoUrl}
          phases={phases}
          corrections={corrections}
          metrics={metrics}
        />
      </section>

      {/* 2. Biomechanics Metrics & Coach Benchmark Comparison */}
      <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl text-slate-100">
        <div className="flex items-center justify-between mb-5 flex-wrap gap-2">
          <div className="flex items-center space-x-2.5">
            <BarChart3 className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-bold text-slate-100">Biomechanical Joint Angles & Kinematics</h2>
          </div>
          <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 rounded-full uppercase tracking-wider">
            {sport} &bull; {movement.replace('_', ' ')}
          </span>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(metrics).map(([key, value]) => {
            if (typeof value === 'object' && value !== null) return null;
            if (key.endsWith('_idx')) return null;

            const bench = benchmarkMetrics[key];
            const label = bench?.metric_name || key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
            const targetRange = bench?.target_range;
            const optimal = bench?.optimal;

            // Check if within reference range
            let statusBadge = null;
            if (targetRange && typeof value === 'number') {
              const inRange = value >= targetRange[0] && value <= targetRange[1];
              statusBadge = inRange ? (
                <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30 flex items-center space-x-1">
                  <CheckCircle className="w-3 h-3" />
                  <span>Optimal</span>
                </span>
              ) : (
                <span className="text-[10px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30 flex items-center space-x-1">
                  <AlertCircle className="w-3 h-3" />
                  <span>Deviation</span>
                </span>
              );
            }

            return (
              <div
                key={key}
                className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      {label}
                    </span>
                    {statusBadge}
                  </div>
                  <div className="text-2xl font-black text-slate-100 mt-1">
                    {typeof value === 'number' ? `${value.toFixed(1)}°` : value}
                  </div>
                </div>

                {targetRange && (
                  <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
                    <span>Reference Target:</span>
                    <strong className="text-cyan-300 font-semibold">
                      {targetRange[0]}° - {targetRange[1]}°
                    </strong>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* 3. Five-Pillar Actionable Corrections & Cautious Insights */}
      {corrections && corrections.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-100">Technique Corrections & Coaching Insights</h2>
              <p className="text-xs text-slate-400">
                Prioritized deviations identified against coach-approved reference baselines.
              </p>
            </div>
            <span className="text-xs font-semibold text-slate-300 bg-slate-800 px-3 py-1 rounded-full border border-slate-700">
              {corrections.length} Identified
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {corrections.map((corr, idx) => (
              <CorrectionCard key={corr.rule_id || idx} correction={corr} />
            ))}
          </div>
        </section>
      )}

      {/* 4. Legacy Video Info / Metadata if available */}
      {result.video_info && (
        <section className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm text-slate-300">
          <div className="flex items-center space-x-2 mb-3">
            <Film className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-slate-200">Video Properties</h3>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <span className="text-slate-500 uppercase text-[10px] block">Resolution</span>
              <span className="font-semibold">{result.video_info.width} × {result.video_info.height}</span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <span className="text-slate-500 uppercase text-[10px] block">Frame Rate</span>
              <span className="font-semibold">{result.video_info.fps} FPS</span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <span className="text-slate-500 uppercase text-[10px] block">Duration</span>
              <span className="font-semibold">{result.video_info.duration_seconds}s</span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <span className="text-slate-500 uppercase text-[10px] block">Frames Processed</span>
              <span className="font-semibold">{result.frames_processed || result.render_meta?.total_frames_rendered || 'All'}</span>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
