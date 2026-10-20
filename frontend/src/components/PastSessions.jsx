import React from 'react';
import { History, CheckCircle, ArrowRight } from 'lucide-react';

export default function PastSessions({ sessions, onLoadSession }) {
  if (!sessions || sessions.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-sm">
      <div className="flex items-center space-x-2.5 pb-4 mb-4 border-b border-slate-100">
        <History className="w-5 h-5 text-indigo-600" />
        <div>
          <h3 className="text-base font-bold text-slate-900">Recent Sessions</h3>
          <p className="text-xs text-slate-500">Quickly reload your previous AI video analyses</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {sessions.slice(0, 6).map((sess) => (
          <div
            key={sess.session_id}
            onClick={() => onLoadSession(sess.session_id)}
            className="p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 hover:bg-indigo-50/40 hover:border-indigo-300 cursor-pointer transition-all flex items-center justify-between group"
          >
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs uppercase">
                {sess.sport?.slice(0, 2) || 'SP'}
              </div>
              <div>
                <p className="text-xs font-bold text-slate-900 capitalize">
                  {sess.sport} Analysis
                </p>
                <p className="text-[11px] text-slate-400">
                  {sess.frames_processed} frames • {sess.timestamp ? new Date(sess.timestamp).toLocaleDateString() : 'Recent'}
                </p>
              </div>
            </div>

            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all" />
          </div>
        ))}
      </div>
    </div>
  );
}
