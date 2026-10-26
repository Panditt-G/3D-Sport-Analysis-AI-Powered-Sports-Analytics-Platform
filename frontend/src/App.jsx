import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import SportSelector from './components/SportSelector';
import VideoUploader from './components/VideoUploader';
import ResultsDashboard from './components/ResultsDashboard';
import PastSessions from './components/PastSessions';
import {
  fetchSports,
  fetchMovements,
  createAnalysisJob,
  pollAnalysisJob,
  getAnnotatedVideoUrl,
  fetchSessions,
  fetchResults,
} from './services/api';

export default function App() {
  const [sports, setSports] = useState([]);
  const [selectedSport, setSelectedSport] = useState('badminton');
  const [movements, setMovements] = useState({});
  const [selectedMovement, setSelectedMovement] = useState('overhead_clear');
  const [selectedModel, setSelectedModel] = useState('mediapipe');

  const [selectedFile, setSelectedFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stageMessage, setStageMessage] = useState(null);
  const [statusType, setStatusType] = useState('info');

  const [analysisResult, setAnalysisResult] = useState(null);
  const [annotatedVideoUrl, setAnnotatedVideoUrl] = useState(null);
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    loadSports();
    loadSessionsList();
  }, []);

  useEffect(() => {
    if (selectedSport) {
      loadSportMovements(selectedSport);
    }
  }, [selectedSport]);

  const loadSports = async () => {
    try {
      const data = await fetchSports();
      setSports(data);
      if (data && data.length > 0 && !selectedSport) {
        setSelectedSport(data[0].name);
      }
    } catch (err) {
      console.error('Failed to load registered sports:', err);
    }
  };

  const loadSportMovements = async (sportName) => {
    try {
      const data = await fetchMovements(sportName);
      if (data && data.movements) {
        setMovements(data.movements);
        const keys = Object.keys(data.movements);
        if (keys.length > 0 && !data.movements[selectedMovement]) {
          setSelectedMovement(keys[0]);
        }
      } else {
        setMovements({});
      }
    } catch (e) {
      setMovements({});
    }
  };

  const loadSessionsList = async () => {
    try {
      const data = await fetchSessions();
      setSessions(data);
    } catch (err) {
      console.log('Sessions load skipped:', err.message);
    }
  };

  const handleSportSelect = (sportName) => {
    setSelectedSport(sportName);
    setAnalysisResult(null);
  };

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setAnalysisResult(null);
  };

  const handleStartAnalysis = async () => {
    if (!selectedSport || !selectedFile) return;

    setIsAnalyzing(true);
    setProgress(5);
    setStageMessage('Uploading video and initializing analysis job...');
    setStatusType('info');
    setAnalysisResult(null);
    setAnnotatedVideoUrl(null);

    try {
      // 1. Create asynchronous job
      const job = await createAnalysisJob(
        selectedFile,
        selectedSport,
        selectedMovement,
        selectedModel
      );

      setStageMessage(`Job ${job.job_id} created. Extracting poses and analyzing biomechanics...`);

      // 2. Poll job until completion
      const results = await pollAnalysisJob(job.job_id, (statusUpdate) => {
        setProgress(statusUpdate.progress_pct || 10);
        setStageMessage(statusUpdate.stage || 'Processing video...');
      });

      // 3. Complete and display
      setProgress(100);
      setAnalysisResult(results);
      setAnnotatedVideoUrl(getAnnotatedVideoUrl(job.job_id));
      setStageMessage(`Analysis completed successfully for ${selectedSport} (${selectedMovement.replace('_', ' ')})!`);
      setStatusType('success');
      loadSessionsList();
    } catch (err) {
      setStageMessage('Analysis failed: ' + err.message);
      setStatusType('error');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleLoadSession = async (sessionId) => {
    try {
      setStageMessage(`Loading session #${sessionId}...`);
      setStatusType('info');
      const res = await fetchResults(sessionId);
      setAnalysisResult(res);
      const vidUrl = res.video_output_url || (res.job_id ? getAnnotatedVideoUrl(res.job_id) : `/api/outputs/${sessionId}_annotated.mp4`);
      setAnnotatedVideoUrl(vidUrl);
      setStageMessage(`Loaded session #${sessionId}`);
      setStatusType('success');
    } catch (err) {
      setStageMessage('Failed to load session: ' + err.message);
      setStatusType('error');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased selection:bg-emerald-500 selection:text-slate-950">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Banner */}
        <div className="bg-gradient-to-r from-emerald-950/40 via-slate-900 to-cyan-950/40 border border-slate-800 rounded-3xl p-6 sm:p-8 relative overflow-hidden">
          <div className="relative z-10 max-w-3xl">
            <span className="text-[11px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 rounded-full uppercase tracking-wider inline-block mb-3">
              Multi-Sport AI Pose Estimation & Biomechanics Platform
            </span>
            <h1 className="text-2xl sm:text-4xl font-extrabold text-slate-100 tracking-tight leading-tight">
              AI Movement Analysis, Coach Reference Alignment & Technique Correction
            </h1>
            <p className="mt-3 text-sm text-slate-400 leading-relaxed">
              Upload athlete footage to extract full-body skeleton landmarks, segment stroke phases, compare against coach-approved references, and review actionable 5-point technique cues.
            </p>
          </div>
        </div>

        {/* 1. Sport & Movement Selection */}
        <SportSelector
          sports={sports}
          selectedSport={selectedSport}
          onSelectSport={handleSportSelect}
          movements={movements}
          selectedMovement={selectedMovement}
          onSelectMovement={setSelectedMovement}
          selectedModel={selectedModel}
          onSelectModel={setSelectedModel}
        />

        {/* 2. Video Upload & Action */}
        <VideoUploader
          selectedSport={selectedSport}
          selectedFile={selectedFile}
          onFileSelect={handleFileSelect}
          onStartAnalysis={handleStartAnalysis}
          isAnalyzing={isAnalyzing}
          progress={progress}
          statusMessage={stageMessage}
          statusType={statusType}
        />

        {/* 3. Interactive Results Dashboard */}
        {analysisResult && (
          <ResultsDashboard
            result={analysisResult}
            videoUrl={annotatedVideoUrl}
          />
        )}

        {/* 4. Past Sessions History */}
        <PastSessions
          sessions={sessions}
          onLoadSession={handleLoadSession}
        />
      </main>
    </div>
  );
}
