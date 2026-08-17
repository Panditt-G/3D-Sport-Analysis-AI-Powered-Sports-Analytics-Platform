import React, { useRef, useState } from 'react';
import { UploadCloud, FileVideo, AlertCircle, Loader2 } from 'lucide-react';

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
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm mb-6">
      <div className="mb-4">
        <h2 className="text-lg font-bold text-slate-800">2. Upload Video</h2>
        <p className="text-xs text-slate-500">Upload video footage for AI pose & telemetry extraction</p>
      </div>

      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-150 ${
          isDragOver
            ? 'border-blue-500 bg-blue-50/50'
            : 'border-slate-300 bg-slate-50/50 hover:border-slate-400 hover:bg-slate-50'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".mp4,.avi,.mov,.mkv,.webm"
          className="hidden"
        />

        <div className="flex flex-col items-center">
          <div className="bg-white p-3 rounded-full border border-slate-200 shadow-sm mb-3 text-blue-600">
            <UploadCloud className="w-8 h-8" />
          </div>
          <p className="text-sm font-semibold text-slate-700">
            Click to browse or drag & drop video here
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Supports MP4, AVI, MOV, MKV, WebM (Max 500 MB)
          </p>
        </div>
      </div>

      {selectedFile && (
        <div className="mt-4 flex items-center justify-between bg-slate-100 p-3 rounded-lg border border-slate-200">
          <div className="flex items-center space-x-3">
            <FileVideo className="w-5 h-5 text-blue-600" />
            <div>
              <p className="text-xs font-semibold text-slate-800">{selectedFile.name}</p>
              <p className="text-[11px] text-slate-500">{fileSizeMb} MB</p>
            </div>
          </div>
          <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
            Ready
          </span>
        </div>
      )}

      {statusMessage && (
        <div
          className={`mt-4 p-3 rounded-lg text-xs flex items-start space-x-2 border ${
            statusType === 'error'
              ? 'bg-rose-50 border-rose-200 text-rose-700'
              : statusType === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
              : 'bg-blue-50 border-blue-200 text-blue-700'
          }`}
        >
          {statusType === 'error' ? (
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          ) : isAnalyzing ? (
            <Loader2 className="w-4 h-4 mt-0.5 shrink-0 animate-spin" />
          ) : null}
          <span>{statusMessage}</span>
        </div>
      )}

      {isAnalyzing && (
        <div className="mt-3 bg-slate-100 rounded-full h-2 overflow-hidden">
          <div
            className="bg-blue-600 h-full transition-all duration-300 rounded-full"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      <div className="mt-5">
        <button
          onClick={onStartAnalysis}
          disabled={!selectedSport || !selectedFile || isAnalyzing}
          className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-lg shadow-sm transition-colors duration-150 flex items-center justify-center space-x-2"
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Analyzing Video...</span>
            </>
          ) : (
            <span>Run Sports AI Analysis</span>
          )}
        </button>
      </div>
    </div>
  );
}
