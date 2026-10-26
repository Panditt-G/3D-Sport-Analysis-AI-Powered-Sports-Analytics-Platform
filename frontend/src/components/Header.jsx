import React from 'react';
import { Activity, Trophy, Sparkles } from 'lucide-react';

export default function Header() {
  return (
    <header className="bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          <div className="bg-gradient-to-tr from-emerald-500 to-cyan-500 text-slate-950 p-2.5 rounded-xl shadow-lg shadow-emerald-500/20">
            <Trophy className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-black text-slate-100 tracking-tight">
                ANTIGRAVITY SPORTS AI
              </h1>
              <span className="text-[10px] font-extrabold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded-full uppercase">
                v2.0 MVP
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              Multi-Sport Biomechanics & Technique Correction Engine
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 bg-emerald-500/10 text-emerald-400 px-3.5 py-1.5 rounded-full text-xs font-bold border border-emerald-500/30">
          <Activity className="w-3.5 h-3.5 animate-pulse text-emerald-400" />
          <span>Core AI Pipeline Active</span>
        </div>
      </div>
    </header>
  );
}
