import React, { useRef, useState } from 'react';
import { UploadCloud, Film, AlertCircle, Sparkles, CheckCircle2 } from 'lucide-react';

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
    <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-100 gap-2">
        <div>
          <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider block mb-0.5">
            Step 2
          </span>
          <h2 className="text-lg font-bold text-slate-900">Upload Video Footage</h2>
          <p className="text-xs text-slate-500">
            Upload match video or training clip to generate automated movement insights
          </p>
        </div>
        {selectedFile && (
          <span className="self-start sm:self-center text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full flex items-center space-x-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Video Ready</span>
          </span>
        )}
      </div>

      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-2xl p-8 sm:p-10 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center ${
          isDragOver
            ? 'border-indigo-500 bg-indigo-50/60 scale-[0.99]'
            : 'border-slate-300 bg-slate-50/60 hover:bg-indigo-50/30 hover:border-indigo-400'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".mp4,.avi,.mov,.mkv,.webm"
          className="hidden"
        />

        <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-500 to-sky-400 text-white flex items-center justify-center shadow-lg shadow-indigo-500/20 mb-4 transition-transform hover:scale-110">
          <UploadCloud className="w-7 h-7" />
        </div>
        <p className="text-sm font-bold text-slate-800">
          Choose a video or drag it here
        </p>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          Supports MP4, AVI, MOV, MKV, WebM formats (up to 500 MB)
        </p>
      </div>

      {selectedFile && (
        <div className="mt-4 flex items-center justify-between bg-slate-50 border border-slate-200 p-3.5 rounded-xl">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center">
              <Film className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-800">{selectedFile.name}</p>
              <p className="text-xs text-slate-500">{fileSizeMb} MB • Video loaded</p>
            </div>
          </div>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onFileSelect(null);
            }}
            className="text-xs font-semibold text-slate-500 hover:text-rose-600 px-3 py-1 hover:bg-slate-100 rounded-lg transition-colors"
          >
            Change
          </button>
        </div>
      )}

      {statusMessage && (
        <div
          className={`mt-4 p-4 rounded-xl text-xs sm:text-sm font-medium flex items-start space-x-3 border ${
            statusType === 'error'
              ? 'bg-rose-50 border-rose-200 text-rose-800'
              : statusType === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-indigo-50 border-indigo-200 text-indigo-900'
          }`}
        >
          {statusType === 'error' ? (
            <AlertCircle className="w-5 h-5 mt-0.5 shrink-0 text-rose-600" />
          ) : (
            <div className="w-4 h-4 mt-0.5 shrink-0 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          )}
          <span className="leading-snug">{statusMessage}</span>
        </div>
      )}

      {isAnalyzing && (
        <div className="mt-4">
          <div className="flex justify-between text-xs font-bold text-slate-600 mb-1.5">
            <span>Analyzing motion kinematics &amp; equipment...</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden p-0.5">
            <div
              className="bg-gradient-to-r from-indigo-500 to-sky-500 h-full rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      <div className="mt-5">
        <button
          onClick={onStartAnalysis}
          disabled={!selectedSport || !selectedFile || isAnalyzing}
          className="w-full py-3.5 px-6 bg-gradient-to-r from-indigo-600 to-sky-600 hover:from-indigo-700 hover:to-sky-700 disabled:from-slate-200 disabled:to-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed text-white text-sm font-bold rounded-xl shadow-md shadow-indigo-600/20 hover:shadow-lg transition-all duration-200 flex items-center justify-center space-x-2"
        >
          {isAnalyzing ? (
            <span>Processing Video...</span>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span className="capitalize">
                Start {selectedSport || 'Sports'} Analysis
              </span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
