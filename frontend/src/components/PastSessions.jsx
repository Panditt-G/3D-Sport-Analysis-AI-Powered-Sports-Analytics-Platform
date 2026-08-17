import React from 'react';
import { History, CheckCircle, AlertCircle } from 'lucide-react';

export default function PastSessions({ sessions, onLoadSession }) {
  if (!sessions || sessions.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm mb-6">
        <div className="flex items-center space-x-2 mb-3">
          <History className="w-5 h-5 text-slate-500" />
          <h2 className="text-lg font-bold text-slate-800">Past Analysis Sessions</h2>
        </div>
        <p className="text-xs text-slate-400">No previous sessions found.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm mb-6">
      <div className="flex items-center space-x-2 mb-4">
        <History className="w-5 h-5 text-blue-600" />
        <h2 className="text-lg font-bold text-slate-800">Past Analysis Sessions</h2>
      </div>

      <div className="divide-y divide-slate-100">
        {sessions.map((sess) => (
          <div
            key={sess.session_id}
            onClick={() => onLoadSession(sess.session_id)}
            className="py-3 flex items-center justify-between hover:bg-slate-50 px-2 rounded-lg cursor-pointer transition-colors"
          >
            <div className="flex items-center space-x-3">
              {sess.status === 'completed' ? (
                <CheckCircle className="w-4 h-4 text-emerald-500" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-500" />
              )}
              <div>
                <p className="text-xs font-bold text-slate-800">
                  Session #{sess.session_id} <span className="font-normal text-slate-500">• {sess.sport}</span>
                </p>
                <p className="text-[11px] text-slate-400">
                  {sess.frames_processed} frames processed
                </p>
              </div>
            </div>

            <span className="text-xs font-mono text-slate-400">
              {sess.timestamp ? new Date(sess.timestamp).toLocaleDateString() : ''}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
