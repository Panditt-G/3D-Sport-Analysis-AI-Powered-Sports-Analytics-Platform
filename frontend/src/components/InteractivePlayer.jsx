import React, { useState, useRef } from 'react';
import { Play, Pause, RotateCcw, Eye, ShieldAlert, Sparkles, Layers, Download } from 'lucide-react';

export const InteractivePlayer = ({ videoUrl, phases = {}, corrections = [], metrics = {} }) => {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [activeLayerGhost, setActiveLayerGhost] = useState(true);
  const [activeLayerCallout, setActiveLayerCallout] = useState(true);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const changeSpeed = (speed) => {
    if (!videoRef.current) return;
    videoRef.current.playbackRate = speed;
    setPlaybackSpeed(speed);
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration || 1);
    }
  };

  const seekTo = (seconds) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      setCurrentTime(seconds);
    }
  };

  // Determine current active phase based on timestamp
  const currentPhase = Object.entries(phases).find(
    ([_, p]) => currentTime >= (p.start_time || 0) && currentTime <= (p.end_time || 999)
  );

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl text-slate-100">
      {/* Top Header Bar */}
      <div className="bg-slate-950/80 px-5 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
            AI Synchronized Biomechanics Player
          </span>
          {currentPhase && (
            <span className="text-[11px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2.5 py-0.5 rounded-full">
              Phase: {currentPhase[1].name || currentPhase[0]}
            </span>
          )}
        </div>

        {/* Layer Toggles */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveLayerGhost(!activeLayerGhost)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              activeLayerGhost
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                : 'bg-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ghost Reference</span>
          </button>
          <button
            onClick={() => setActiveLayerCallout(!activeLayerCallout)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              activeLayerCallout
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                : 'bg-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>HUD Telemetry</span>
          </button>
        </div>
      </div>

      {/* Video Container */}
      <div 
        className="relative bg-black aspect-video flex items-center justify-center cursor-pointer group"
        onClick={togglePlay}
      >
        {videoUrl ? (
          <>
            <video
              ref={videoRef}
              src={videoUrl}
              className="w-full h-full object-contain"
              preload="auto"
              onTimeUpdate={handleTimeUpdate}
              onLoadedMetadata={handleLoadedMetadata}
              onEnded={() => setIsPlaying(false)}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              playsInline
            />
            {/* Big Centered Play Button Overlay when paused */}
            {!isPlaying && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/30 backdrop-blur-[2px] transition group-hover:bg-black/20">
                <div className="w-16 h-16 rounded-full bg-emerald-500/90 hover:bg-emerald-400 text-slate-950 flex items-center justify-center shadow-2xl shadow-emerald-500/50 transform group-hover:scale-110 transition">
                  <Play className="w-8 h-8 fill-current ml-1" />
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-slate-500 text-sm flex flex-col items-center space-y-2">
            <Eye className="w-8 h-8 opacity-40 animate-pulse" />
            <span>Video processing or loading...</span>
          </div>
        )}
      </div>

      {/* Movement Timeline Phase Markers */}
      <div className="px-5 pt-3 bg-slate-950/60 border-t border-slate-800/80">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
          <span>Stroke Phases</span>
          <span>
            {currentTime.toFixed(2)}s / {duration.toFixed(2)}s
          </span>
        </div>

        {/* Phase Timeline Track */}
        <div className="relative h-6 bg-slate-800 rounded-md overflow-hidden flex items-center cursor-pointer mb-2">
          {Object.entries(phases).map(([pid, pdata], idx) => {
            const pStart = pdata.start_time || 0;
            const pEnd = pdata.end_time || duration;
            const leftPct = duration > 0 ? (pStart / duration) * 100 : idx * 16.6;
            const widthPct = duration > 0 ? Math.max(5, ((pEnd - pStart) / duration) * 100) : 16.6;

            const isCurrent = currentPhase && currentPhase[0] === pid;

            return (
              <div
                key={pid}
                onClick={() => seekTo(pStart)}
                style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
                className={`absolute top-0 bottom-0 border-r border-slate-900/60 flex items-center justify-center px-1 text-[10px] font-bold transition hover:opacity-100 ${
                  isCurrent
                    ? 'bg-emerald-500/50 text-white border-b-2 border-emerald-400'
                    : 'bg-slate-700/60 text-slate-300 hover:bg-slate-700'
                }`}
                title={`${pdata.name || pid}: ${pStart.toFixed(2)}s - ${pEnd.toFixed(2)}s`}
              >
                <span className="truncate">{pdata.name || pid}</span>
              </div>
            );
          })}
        </div>

        {/* Scrubber slider */}
        <input
          type="range"
          min="0"
          max={duration || 1}
          step="0.01"
          value={currentTime}
          onChange={(e) => seekTo(parseFloat(e.target.value))}
          className="w-full accent-emerald-500 cursor-pointer mb-3"
        />
      </div>

      {/* Playback Controls Footer */}
      <div className="bg-slate-950 px-5 py-3 border-t border-slate-800 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center space-x-3">
          <button
            onClick={togglePlay}
            className="p-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold transition flex items-center space-x-1"
          >
            {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current" />}
          </button>
          <button
            onClick={() => seekTo(0)}
            className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Restart"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        {/* Controls right side: Speed & Download */}
        <div className="flex items-center space-x-3">
          {/* Slow Motion Speed Selector */}
          <div className="flex items-center space-x-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800">
            <span className="text-[11px] font-semibold text-slate-400 px-2 uppercase">Speed</span>
            {[0.25, 0.5, 1.0].map((speed) => (
              <button
                key={speed}
                onClick={() => changeSpeed(speed)}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition ${
                  playbackSpeed === speed
                    ? 'bg-emerald-500 text-slate-950 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {speed}x
              </button>
            ))}
          </div>

          {videoUrl && (
            <a
              href={videoUrl}
              download="annotated_movement.mp4"
              className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-emerald-400 border border-slate-800 transition flex items-center space-x-1.5 text-xs font-semibold"
              title="Download Annotated MP4"
            >
              <Download className="w-4 h-4" />
              <span className="hidden sm:inline">Export</span>
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default InteractivePlayer;
