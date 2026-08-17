import React from 'react';
import { Activity, Trophy } from 'lucide-react';

export default function Header() {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-blue-600 text-white p-2 rounded-lg shadow-sm">
            <Trophy className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800 leading-tight">
              Sports AI Analytics Platform
            </h1>
            <p className="text-xs text-slate-500 font-medium">
              Multi-Sport Computer Vision & Biomechanics Analysis
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-full text-xs font-semibold border border-emerald-200">
          <Activity className="w-4 h-4 animate-pulse" />
          <span>System Ready</span>
        </div>
      </div>
    </header>
  );
}
