import React from 'react';
import { Video, Download, CheckCircle2, Film } from 'lucide-react';

export default function ResultsDashboard({ result }) {
  if (!result) return null;

  const { video_output_url, video_info, sport, frames_processed, session_id } = result;

  // Build absolute URL: dev mode runs on 5173 (proxied), but static files must hit 7860 directly
  const backendBase = window.location.port === '5173' ? 'http://localhost:7860' : '';
  const videoSrc = video_output_url ? `${backendBase}${video_output_url}` : null;

  // Determine MIME type based on actual extension
  const mimeType = videoSrc && videoSrc.endsWith('.avi') ? 'video/x-msvideo' : 'video/mp4';

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-sky-500 text-white flex items-center justify-center shadow-md shadow-indigo-500/20">
            <Video className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-slate-900">AI Video Output</h2>
              <span className="text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded-full flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>Done</span>
              </span>
            </div>
            <p className="text-xs text-slate-500">
              AI detections &amp; telemetry rendered as black text directly onto every frame
            </p>
          </div>
        </div>

        {videoSrc && (
          <a
            href={videoSrc}
            download
            className="inline-flex items-center space-x-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200/80 px-4 py-2 rounded-xl text-xs font-bold transition-colors shadow-sm self-start sm:self-center"
          >
            <Download className="w-4 h-4" />
            <span>Download Annotated Video</span>
          </a>
        )}
      </div>

      {/* Video Player */}
      <div className="relative rounded-2xl overflow-hidden bg-slate-950 border border-slate-800 shadow-inner flex flex-col items-center justify-center min-h-[360px]">
        {videoSrc ? (
          <video
            controls
            autoPlay
            loop
            muted
            className="w-full max-h-[580px] object-contain"
            key={videoSrc}
          >
            <source src={videoSrc} type={mimeType} />
            Your browser does not support the video tag. <a href={videoSrc} className="text-indigo-400 underline">Download the video instead</a>.
          </video>
        ) : (
          <div className="text-center p-8 text-slate-400">
            <Film className="w-12 h-12 mx-auto mb-3 opacity-40 text-indigo-400 animate-pulse" />
            <p className="text-sm font-semibold">Generating annotated video output...</p>
          </div>
        )}
      </div>

      {/* Video Metadata */}
      {video_info && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-slate-50 border border-slate-100 p-3 rounded-xl text-center">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide block mb-0.5">Sport</span>
            <span className="text-sm font-bold text-slate-800 capitalize">{sport}</span>
          </div>
          <div className="bg-slate-50 border border-slate-100 p-3 rounded-xl text-center">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide block mb-0.5">Resolution</span>
            <span className="text-sm font-bold text-slate-800">{video_info.width} × {video_info.height}</span>
          </div>
          <div className="bg-slate-50 border border-slate-100 p-3 rounded-xl text-center">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide block mb-0.5">Frame Rate</span>
            <span className="text-sm font-bold text-slate-800">{video_info.fps} FPS</span>
          </div>
          <div className="bg-slate-50 border border-slate-100 p-3 rounded-xl text-center">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide block mb-0.5">Frames Processed</span>
            <span className="text-sm font-bold text-indigo-600">{frames_processed}</span>
          </div>
        </div>
      )}
    </div>
  );
}
