import React from 'react';
import { CheckCircle2, Crosshair, Cpu } from 'lucide-react';

const SPORT_ICONS = {
  badminton: '🏸',
  running: '🏃',
  table_tennis: '🏓',
  tennis: '🎾',
  gym: '🏋️',
};

export default function SportSelector({
  sports,
  selectedSport,
  onSelectSport,
  movements = {},
  selectedMovement,
  onSelectMovement,
  selectedModel,
  onSelectModel,
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6 text-slate-100">
      {/* 1. Sport Selection */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <h2 className="text-base font-bold text-slate-100">1. Select Sport Pack</h2>
          <p className="text-xs text-slate-400">Choose a validated biomechanics module</p>
        </div>
        {selectedSport && (
          <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 rounded-full uppercase tracking-wider">
            Active: {selectedSport}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 mb-6">
        {sports.map((sport) => {
          const isSelected = selectedSport === sport.name;
          const icon = SPORT_ICONS[sport.name] || '🏅';

          return (
            <button
              key={sport.name}
              onClick={() => onSelectSport(sport.name)}
              className={`relative flex flex-col items-center p-4 rounded-xl border text-center transition-all ${
                isSelected
                  ? 'border-emerald-500 bg-emerald-500/10 ring-2 ring-emerald-500/30 shadow-lg'
                  : 'border-slate-800 bg-slate-950/60 hover:border-slate-700 hover:bg-slate-800/40 text-slate-400'
              }`}
            >
              {isSelected && <CheckCircle2 className="w-4 h-4 text-emerald-400 absolute top-2 right-2" />}
              <span className="text-3xl mb-2">{icon}</span>
              <span className="font-bold text-sm text-slate-100">{sport.display_name}</span>
              <span className="text-[10px] text-slate-400 mt-1 uppercase tracking-wider">
                {sport.version ? `v${sport.version}` : 'Sport Pack'}
              </span>
            </button>
          );
        })}
      </div>

      {/* 2. Movement & Pose Model Config */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-800/80">
        {/* Movement Selector */}
        <div>
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-2 flex items-center space-x-1.5">
            <Crosshair className="w-3.5 h-3.5 text-emerald-400" />
            <span>Target Movement / Stroke</span>
          </label>
          <select
            value={selectedMovement}
            onChange={(e) => onSelectMovement && onSelectMovement(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs font-semibold text-slate-200 focus:outline-none focus:border-emerald-500 transition"
          >
            {Object.keys(movements).length > 0 ? (
              Object.entries(movements).map(([id, m]) => (
                <option key={id} value={id}>
                  {m.name || id.replace('_', ' ').title()}
                </option>
              ))
            ) : (
              <option value="overhead_clear">Overhead Clear (Full Phase Analysis)</option>
            )}
          </select>
        </div>

        {/* Model Selection */}
        <div>
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-2 flex items-center space-x-1.5">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>Human Pose Estimator Backend</span>
          </label>
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel && onSelectModel(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs font-semibold text-slate-200 focus:outline-none focus:border-cyan-500 transition"
          >
            <option value="mediapipe">MediaPipe BlazePose (CPU-optimized, 33 3D landmarks)</option>
            <option value="yolo">YOLOv8n-pose (Ultra-fast, COCO-17 keypoints)</option>
          </select>
        </div>
      </div>
    </div>
  );
}
