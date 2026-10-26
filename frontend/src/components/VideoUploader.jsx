import React, { useRef, useState } from 'react';
import { UploadCloud, FileVideo, AlertCircle, Loader2, Play, Sparkles } from 'lucide-react';

export default function VideoUploader({
  selectedSport,
  selectedFile,
  onFileSelect,
  onStartAnalysis,
  isAnalyzing,
  statusMessage,
  statusType,
  progress,
}) {
  const fileInputRef = useRef(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(e.target.files[0]);
    }
  };

  const fileSizeMb = selectedFile
    ? (selectedFile.size / (1024 * 1024)).toFixed(2)
    : null;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6 text-slate-100">
      <div className="mb-4">
        <h2 className="text-base font-bold text-slate-100">2. Ingest Athlete Video</h2>
        <p className="text-xs text-slate-400">Supported formats: MP4, AVI, MOV (under 100MB)</p>
      </div>

      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
          isDragOver
            ? 'border-emerald-500 bg-emerald-500/10'
            : 'border-slate-800 bg-slate-950/60 hover:border-slate-700 hover:bg-slate-900'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={handleFileChange}
        />

        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl text-emerald-400">
            <UploadCloud className="w-8 h-8" />
          </div>

          <div>
            <span className="text-sm font-bold text-slate-200">
              {selectedFile ? selectedFile.name : 'Click to select or drag video file here'}
            </span>
            <p className="text-xs text-slate-500 mt-1">
              Side-view or diagonal-rear camera angle recommended for highest biomechanical accuracy
            </p>
          </div>

          {selectedFile && (
            <div className="flex items-center space-x-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700 text-xs">
              <FileVideo className="w-4 h-4 text-emerald-400" />
              <span className="text-slate-300 font-semibold">{fileSizeMb} MB</span>
            </div>
          )}
        </div>
      </div>

      {/* Progress & Stage Status */}
      {isAnalyzing && (
        <div className="mt-5 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-emerald-400 flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>{statusMessage || 'Processing AI pipeline...'}</span>
            </span>
            <span className="text-slate-400">{progress}%</span>
          </div>

          <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
            <div
              className="bg-gradient-to-r from-emerald-500 to-cyan-500 h-full rounded-full transition-all duration-300 shadow-sm"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Static status message if not analyzing */}
      {!isAnalyzing && statusMessage && (
        <div
          className={`mt-4 p-3 rounded-xl border text-xs font-semibold flex items-center space-x-2 ${
            statusType === 'error'
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
          }`}
        >
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Action Button */}
      <div className="mt-5 flex justify-end">
        <button
          onClick={onStartAnalysis}
          disabled={!selectedFile || isAnalyzing}
          className={`px-6 py-3 rounded-xl font-bold text-xs uppercase tracking-wider flex items-center space-x-2 transition shadow-lg ${
            !selectedFile || isAnalyzing
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50'
              : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-emerald-500/20'
          }`}
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Analyzing Movement...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Run Biomechanical Analysis</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
