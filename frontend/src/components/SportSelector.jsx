import React from 'react';
import { Check, Zap } from 'lucide-react';

export default function SportSelector({ sports, selectedSport, onSelectSport }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-100 gap-2">
        <div>
          <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider block mb-0.5">
            Step 1
          </span>
          <h2 className="text-lg font-bold text-slate-900">Choose Your Sport</h2>
          <p className="text-xs text-slate-500">
            Select an activity to load its specialized AI detection model
          </p>
        </div>
        {selectedSport && (
          <div className="self-start sm:self-center flex items-center space-x-1.5 bg-indigo-50 border border-indigo-200/60 px-3 py-1 rounded-full text-xs font-bold text-indigo-700">
            <Zap className="w-3.5 h-3.5 text-indigo-600" />
            <span className="capitalize">{selectedSport} Active</span>
          </div>
        )}
      </div>

      {sports.length === 0 ? (
        <div className="text-center py-8 text-slate-400 text-sm">
          Loading sports models...
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {sports.map((sport) => {
            const isSelected = selectedSport === sport.name;
            const isBadminton = sport.name === 'badminton';

            return (
              <button
                key={sport.name}
                type="button"
                onClick={() => onSelectSport(sport.name)}
                className={`relative p-5 rounded-xl border text-left transition-all duration-200 flex flex-col justify-between group ${
                  isSelected
                    ? 'border-indigo-600 bg-gradient-to-br from-indigo-50/70 via-white to-sky-50/40 ring-2 ring-indigo-600/20 shadow-md'
                    : 'border-slate-200 bg-slate-50/50 hover:bg-white hover:border-slate-300 hover:shadow-sm'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div
                        className={`w-11 h-11 rounded-xl flex items-center justify-center text-2xl transition-transform group-hover:scale-105 shadow-sm ${
                          isSelected
                            ? 'bg-indigo-600 text-white'
                            : 'bg-white border border-slate-200'
                        }`}
                      >
                        {sport.icon || '🏅'}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-base text-slate-900">
                            {sport.display_name}
                          </span>
                          {isBadminton && (
                            <span className="text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200 px-2 py-0.5 rounded-full">
                              Featured
                            </span>
                          )}
                        </div>
                        <span className="text-[11px] font-medium text-slate-400">
                          AI Model Ready
                        </span>
                      </div>
                    </div>

                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center transition-colors ${
                        isSelected
                          ? 'bg-indigo-600 text-white shadow-sm'
                          : 'border border-slate-300 bg-white'
                      }`}
                    >
                      {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed mb-4">
                    {sport.description}
                  </p>
                </div>

                {sport.metrics && sport.metrics.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-3 border-t border-slate-200/60">
                    {sport.metrics.slice(0, 4).map((m) => (
                      <span
                        key={m}
                        className="text-[10px] font-semibold bg-white border border-slate-200 text-slate-600 px-2.5 py-0.5 rounded-md"
                      >
                        {m.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
