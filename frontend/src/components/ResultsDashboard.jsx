import React from 'react';
import { BarChart3, Film, ListFilter } from 'lucide-react';

export default function ResultsDashboard({ result }) {
  if (!result) return null;

  const { video_info, summary, frame_results, sport, frames_processed } = result;

  return (
    <div className="space-y-6">
      {/* Video Info Section */}
      {video_info && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center space-x-2 mb-4">
            <Film className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-bold text-slate-800">Video Metadata</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Resolution</span>
              <span className="text-sm font-bold text-slate-700">{video_info.width} × {video_info.height}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Frame Rate</span>
              <span className="text-sm font-bold text-slate-700">{video_info.fps} FPS</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Duration</span>
              <span className="text-sm font-bold text-slate-700">{video_info.duration_seconds}s</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Frames Processed</span>
              <span className="text-sm font-bold text-slate-700">{frames_processed}</span>
            </div>
          </div>
        </div>
      )}

      {/* Summary Metrics Section */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-bold text-slate-800">AI Summary Metrics</h2>
          </div>
          <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2.5 py-1 rounded border border-blue-100 uppercase">
            {sport}
          </span>
        </div>

        {summary && Object.keys(summary).length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {Object.entries(summary).map(([key, value]) => {
              if (typeof value === 'object' && value !== null) return null;

              const label = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
              let formattedVal = value;
              if (typeof value === 'number') {
                formattedVal = Number.isInteger(value) ? value : value.toFixed(2);
              }

              return (
                <div key={key} className="bg-slate-50 p-4 rounded-xl border border-slate-200/80 text-center">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    {label}
                  </span>
                  <span className="text-2xl font-extrabold text-slate-800">
                    {formattedVal}
                  </span>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-slate-400 italic">No summary metrics computed.</p>
        )}
      </div>

      {/* Frame Results Table */}
      {frame_results && frame_results.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <ListFilter className="w-5 h-5 text-blue-600" />
              <h2 className="text-lg font-bold text-slate-800">Frame Telemetry Sample</h2>
            </div>
            <span className="text-xs text-slate-400">
              Showing first {Math.min(frame_results.length, 30)} of {frame_results.length} frames
            </span>
          </div>

          <div className="overflow-x-auto border border-slate-200 rounded-lg">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 border-b border-slate-200 text-slate-600 font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Frame</th>
                  <th className="py-2.5 px-3">Time (s)</th>
                  <th className="py-2.5 px-3">Pipeline Detection</th>
                  <th className="py-2.5 px-3">Analytics Telemetry</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {frame_results.slice(0, 30).map((row, idx) => {
                  const detStr = Object.entries(row.detection || {})
                    .filter(([k]) => !['frame_idx', 'timestamp'].includes(k))
                    .map(([k, v]) => `${k}: ${v}`)
                    .join(', ') || '-';

                  const metStr = Object.entries(row.metrics || {})
                    .map(([k, v]) => `${k}: ${v}`)
                    .join(', ') || '-';

                  return (
                    <tr key={idx} className="hover:bg-slate-50 transition-colors">
                      <td className="py-2 px-3 font-mono font-medium">{row.frame_idx}</td>
                      <td className="py-2 px-3 font-mono">{row.timestamp?.toFixed(3)}</td>
                      <td className="py-2 px-3 font-mono text-slate-600">{detStr}</td>
                      <td className="py-2 px-3 font-mono text-slate-600">{metStr}</td>
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
