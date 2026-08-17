import React from 'react';
import { CheckCircle2 } from 'lucide-react';

export default function SportSelector({ sports, selectedSport, onSelectSport }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-800">1. Select Sport</h2>
          <p className="text-xs text-slate-500">Choose a sport pipeline for targeted AI analysis</p>
        </div>
        {selectedSport && (
          <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-md border border-blue-100 uppercase tracking-wide">
            Selected: {selectedSport}
          </span>
        )}
      </div>

      {sports.length === 0 ? (
        <div className="text-center py-8 text-slate-400 text-sm">
          Loading registered sports...
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          {sports.map((sport) => {
            const isSelected = selectedSport === sport.name;
            return (
              <button
                key={sport.name}
                onClick={() => onSelectSport(sport.name)}
                className={`relative flex flex-col items-center p-4 rounded-lg border text-left transition-all duration-150 ${
                  isSelected
                    ? 'border-blue-600 bg-blue-50/50 ring-2 ring-blue-600/20 shadow-sm'
                    : 'border-slate-200 bg-slate-50/50 hover:border-slate-300 hover:bg-slate-50'
                }`}
              >
                {isSelected && (
                  <CheckCircle2 className="w-4 h-4 text-blue-600 absolute top-2 right-2" />
                )}
                <span className="text-3xl mb-2">{sport.icon || '🏅'}</span>
                <span className="font-semibold text-sm text-slate-800 text-center">
                  {sport.display_name}
                </span>
                <span className="text-[11px] text-slate-500 text-center line-clamp-2 mt-1">
                  {sport.description}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
