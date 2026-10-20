import React from 'react';
import { BarChart3, Film, ListFilter, CheckCircle, Flame, Target, Compass } from 'lucide-react';

export default function ResultsDashboard({ result }) {
  if (!result) return null;

  const { video_info, summary, frame_results, sport, frames_processed } = result;

  return (
    <div className="space-y-6">
      {/* Summary KPI Cards with Vibrant Gradients */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-sm">
        <div className="flex items-center justify-between pb-4 mb-5 border-b border-slate-100">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Performance Summary</h2>
              <p className="text-xs text-slate-500">Key AI analytics &amp; metric calculations</p>
            </div>
          </div>
          <span className="text-xs font-bold text-indigo-700 bg-indigo-50 border border-indigo-200/60 px-3 py-1 rounded-full uppercase tracking-wide">
            {sport}
          </span>
        </div>

        {summary && Object.keys(summary).length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {Object.entries(summary).map(([key, value], idx) => {
              if (typeof value === 'object' && value !== null) return null;

              const label = key.replace(/_/g, ' ');
              let formattedVal = value;
              if (typeof value === 'number') {
                formattedVal = Number.isInteger(value) ? value : value.toFixed(2);
              }

              // Card gradient accents
              const cardAccents = [
                'from-indigo-50/70 to-indigo-100/30 border-indigo-100 text-indigo-900',
                'from-sky-50/70 to-sky-100/30 border-sky-100 text-sky-900',
                'from-emerald-50/70 to-emerald-100/30 border-emerald-100 text-emerald-900',
                'from-violet-50/70 to-violet-100/30 border-violet-100 text-violet-900',
              ];
              const accent = cardAccents[idx % cardAccents.length];

              return (
                <div
                  key={key}
                  className={`bg-gradient-to-br ${accent} p-4 rounded-xl border flex flex-col justify-between`}
                >
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-1">
                    {label}
                  </span>
                  <span className="text-2xl sm:text-3xl font-extrabold text-slate-900">
                    {formattedVal}
                  </span>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-slate-400 italic">No summary metrics generated.</p>
        )}
      </div>

      {/* Video Metadata Cards */}
      {video_info && (
        <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-sm">
          <div className="flex items-center space-x-2.5 pb-3 mb-4 border-b border-slate-100">
            <Film className="w-5 h-5 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-900">Video Information</h3>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-50 border border-slate-100 p-3.5 rounded-xl">
              <span className="text-[11px] font-medium text-slate-400 block mb-0.5">Resolution</span>
              <span className="text-sm font-bold text-slate-800">{video_info.width} × {video_info.height}</span>
            </div>
            <div className="bg-slate-50 border border-slate-100 p-3.5 rounded-xl">
              <span className="text-[11px] font-medium text-slate-400 block mb-0.5">Frame Rate</span>
              <span className="text-sm font-bold text-slate-800">{video_info.fps} FPS</span>
            </div>
            <div className="bg-slate-50 border border-slate-100 p-3.5 rounded-xl">
              <span className="text-[11px] font-medium text-slate-400 block mb-0.5">Duration</span>
              <span className="text-sm font-bold text-slate-800">{video_info.duration_seconds} sec</span>
            </div>
            <div className="bg-slate-50 border border-slate-100 p-3.5 rounded-xl">
              <span className="text-[11px] font-medium text-slate-400 block mb-0.5">Frames Processed</span>
              <span className="text-sm font-bold text-indigo-600">{frames_processed}</span>
            </div>
          </div>
        </div>
      )}

      {/* Frame Table Sample */}
      {frame_results && frame_results.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <ListFilter className="w-5 h-5 text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900">Telemetry Frame Log</h3>
            </div>
            <span className="text-xs text-slate-400">
              Showing first {Math.min(frame_results.length, 25)} of {frame_results.length} frames
            </span>
          </div>

          <div className="overflow-x-auto border border-slate-200 rounded-xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                <tr>
                  <th className="py-2.5 px-3.5">Frame</th>
                  <th className="py-2.5 px-3.5">Time (s)</th>
                  <th className="py-2.5 px-3.5">Detections</th>
                  <th className="py-2.5 px-3.5">Metrics</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {frame_results.slice(0, 25).map((row, idx) => {
                  const detStr = Object.entries(row.detection || {})
                    .filter(([k]) => !['frame_idx', 'timestamp'].includes(k))
                    .map(([k, v]) => `${k}: ${v}`)
                    .join(', ') || '-';

                  const metStr = Object.entries(row.metrics || {})
                    .map(([k, v]) => `${k}: ${v}`)
                    .join(', ') || '-';

                  return (
                    <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-2.5 px-3.5 font-semibold text-slate-900">{row.frame_idx}</td>
                      <td className="py-2.5 px-3.5 text-slate-500">{row.timestamp?.toFixed(2)}s</td>
                      <td className="py-2.5 px-3.5 text-slate-600">{detStr}</td>
                      <td className="py-2.5 px-3.5 text-slate-600">{metStr}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
