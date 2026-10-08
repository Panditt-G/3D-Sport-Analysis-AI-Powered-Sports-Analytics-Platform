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

  const loadSessionsList = () => {
    try {
      const savedSessions = localStorage.getItem('sports_ai_sessions');
      if (savedSessions) {
        setSessions(JSON.parse(savedSessions));
      }
    } catch (err) {
      console.log('Local sessions load skipped:', err.message);
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
    setStatusMessage(`Uploading video for ${selectedSport}...`);
    setStatusType('info');
    setAnalysisResult(null);

    try {
      // 1. Upload and start background processing
      const initialResult = await analyzeVideo(selectedSport, selectedFile);
      setProgress(40);

      if (initialResult.status === 'error') {
        setStatusMessage('Analysis failed to start: ' + (initialResult.error || 'Unknown error'));
        setStatusType('error');
        setIsAnalyzing(false);
        return;
      }

      const sessionId = initialResult.session_id;
      setStatusMessage(`AI is processing video in background. Session: ${sessionId}...`);

      // 2. Poll the server every 3 seconds until completed
      const pollInterval = setInterval(async () => {
        try {
          const result = await fetchResults(sessionId);
          
          if (result && result.status !== 'processing') {
            clearInterval(pollInterval);
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
              
              // Save session locally to browser cache (localStorage)
              const newSession = {
                session_id: result.session_id,
                sport: result.sport,
                status: result.status,
                frames_processed: result.frames_processed,
                timestamp: result.timestamp || new Date().toISOString()
              };
              const existingSessions = JSON.parse(localStorage.getItem('sports_ai_sessions') || '[]');
              const updatedSessions = [newSession, ...existingSessions];
              localStorage.setItem('sports_ai_sessions', JSON.stringify(updatedSessions));

              loadSessionsList();
            }
            setIsAnalyzing(false);
          } else {
            // Still processing, update progress bar artificially
            setProgress((prev) => (prev < 90 ? prev + 5 : 90));
          }
        } catch (err) {
          // If 404, it might still be initializing, just wait for the next tick
          console.log("Polling...", err.message);
        }
      }, 3000);

    } catch (err) {
      setStatusMessage('Error starting analysis: ' + err.message);
      setStatusType('error');
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
