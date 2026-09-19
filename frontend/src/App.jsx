import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import SportSelector from './components/SportSelector';
import VideoUploader from './components/VideoUploader';
import ResultsDashboard from './components/ResultsDashboard';
import PastSessions from './components/PastSessions';
import { fetchSports, analyzeVideo, fetchSessions, fetchResults } from './services/api';

export default function App() {
  const [sports, setSports] = useState([]);
  const [selectedSport, setSelectedSport] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState(null);
  const [statusType, setStatusType] = useState('info');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    loadSports();
    loadSessionsList();
  }, []);

  const loadSports = async () => {
    try {
      const data = await fetchSports();
      setSports(data);
      if (data && data.length > 0 && !selectedSport) {
        // Auto-select running or first available sport
        const runningSport = data.find((s) => s.name === 'running');
        setSelectedSport(runningSport ? runningSport.name : data[0].name);
      }
    } catch (err) {
      setStatusMessage('Failed to load registered sports: ' + err.message);
      setStatusType('error');
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
    setStatusMessage(null);
  };

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setStatusMessage(null);
  };

  const handleStartAnalysis = async () => {
    if (!selectedSport || !selectedFile) return;

    setIsAnalyzing(true);
    setProgress(20);
    setStatusMessage(`Running AI analysis pipeline for ${selectedSport}...`);
    setStatusType('info');
    setAnalysisResult(null);

    try {
      setProgress(60);
      const result = await analyzeVideo(selectedSport, selectedFile);
      setProgress(100);

      if (result.status === 'error') {
        setStatusMessage('Analysis failed: ' + (result.error || 'Unknown error'));
        setStatusType('error');
      } else {
        setAnalysisResult(result);
        setStatusMessage(
          `Analysis complete! Session ID: ${result.session_id} (${result.frames_processed} frames)`
        );
        setStatusType('success');
        loadSessionsList();
      }
    } catch (err) {
      setStatusMessage('Error during analysis: ' + err.message);
      setStatusType('error');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleLoadSession = async (sessionId) => {
    try {
      setStatusMessage(`Loading session #${sessionId}...`);
      setStatusType('info');
      const res = await fetchResults(sessionId);
      setAnalysisResult(res);
      setStatusMessage(`Loaded session #${sessionId}`);
      setStatusType('success');
    } catch (err) {
      setStatusMessage('Failed to load session: ' + err.message);
      setStatusType('error');
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />

      <main className="max-w-6xl mx-auto px-4 py-8 flex-1 w-full space-y-6">
        <SportSelector
          sports={sports}
          selectedSport={selectedSport}
          onSelectSport={handleSportSelect}
        />

        <VideoUploader
          selectedSport={selectedSport}
          selectedFile={selectedFile}
          onFileSelect={handleFileSelect}
          onStartAnalysis={handleStartAnalysis}
          isAnalyzing={isAnalyzing}
          statusMessage={statusMessage}
          statusType={statusType}
          progress={progress}
        />

        {analysisResult && <ResultsDashboard result={analysisResult} />}

        <PastSessions sessions={sessions} onLoadSession={handleLoadSession} />
      </main>

      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        Sports AI Analytics Platform • Built with React & Tailwind CSS v3
      </footer>
    </div>
  );
}
