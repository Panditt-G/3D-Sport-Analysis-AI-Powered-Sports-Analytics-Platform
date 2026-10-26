import React from 'react';
import { History, CheckCircle, AlertCircle } from 'lucide-react';

export default function PastSessions({ sessions, onLoadSession }) {
  if (!sessions || sessions.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6 text-slate-100">
        <div className="flex items-center space-x-2 mb-2">
          <History className="w-4 h-4 text-slate-400" />
          <h2 className="text-sm font-bold text-slate-200">Past Analysis Sessions</h2>
        </div>
        <p className="text-xs text-slate-500">No previous sessions found.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6 text-slate-100">
      <div className="flex items-center space-x-2 mb-4">
        <History className="w-4 h-4 text-emerald-400" />
        <h2 className="text-sm font-bold text-slate-200">Past Analysis Sessions</h2>
      </div>

      <div className="divide-y divide-slate-800">
        {sessions.map((sess) => (
          <div
            key={sess.session_id}
            onClick={() => onLoadSession(sess.session_id)}
            className="py-3 flex items-center justify-between hover:bg-slate-800/50 px-3 rounded-xl cursor-pointer transition"
          >
            <div className="flex items-center space-x-3">
              {sess.status === 'completed' ? (
                <CheckCircle className="w-4 h-4 text-emerald-400" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-400" />
              )}
              <div>
                <p className="text-xs font-bold text-slate-200">
                  Session #{sess.session_id} <span className="font-normal text-slate-400">• {sess.sport}</span>
                </p>
                <p className="text-[11px] text-slate-500">
                  {sess.frames_processed} frames processed
                </p>
              </div>
            </div>

            <span className="text-[11px] font-mono text-slate-500">
              {sess.timestamp ? new Date(sess.timestamp).toLocaleDateString() : ''}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
