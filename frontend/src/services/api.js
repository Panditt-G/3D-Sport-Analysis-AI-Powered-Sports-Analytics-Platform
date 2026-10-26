const API_BASE = '/api';
const API_V1 = '/api/v1';

export const fetchSports = async () => {
  const res = await fetch(`${API_V1}/sports`);
  if (!res.ok) {
    // Fallback to legacy
    const fallbackRes = await fetch(`${API_BASE}/sports`);
    if (!fallbackRes.ok) throw new Error('Failed to fetch registered sports');
    const data = await fallbackRes.json();
    return data.sports;
  }
  const data = await res.json();
  return data.sports;
};

export const fetchMovements = async (sportName) => {
  const res = await fetch(`${API_V1}/sports/${sportName}/movements`);
  if (!res.ok) return null;
  return await res.json();
};

export const fetchReference = async (sportName, movementName) => {
  const res = await fetch(`${API_V1}/references/${sportName}/${movementName}`);
  if (!res.ok) return null;
  return await res.json();
};

export const createAnalysisJob = async (file, sport = 'badminton', movement = 'overhead_clear', poseModel = 'mediapipe') => {
  const formData = new FormData();
  formData.append('file', file);

  const url = `${API_V1}/analyses?sport=${encodeURIComponent(sport)}&movement=${encodeURIComponent(movement)}&pose_model=${encodeURIComponent(poseModel)}`;
  const res = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to initialize analysis job');
  }

  return await res.json();
};

export const pollAnalysisJob = async (jobId, onProgress) => {
  const maxAttempts = 120; // up to 2 minutes
  let attempts = 0;

  while (attempts < maxAttempts) {
    const res = await fetch(`${API_V1}/analyses/${jobId}`);
    if (!res.ok) throw new Error(`Job status check failed: ${res.statusText}`);

    const statusData = await res.json();
    if (onProgress) {
      onProgress(statusData);
    }

    if (statusData.status === 'completed') {
      const resultsRes = await fetch(`${API_V1}/analyses/${jobId}/results`);
      if (!resultsRes.ok) throw new Error('Failed to load final analysis results');
      const fullResults = await resultsRes.json();
      return fullResults.results;
    }

    if (statusData.status === 'failed') {
      throw new Error(statusData.error || statusData.stage || 'Analysis job failed');
    }

    await new Promise((resolve) => setTimeout(resolve, 1000));
    attempts++;
  }

  throw new Error('Analysis timed out. Please try with a shorter video clip.');
};

export const getAnnotatedVideoUrl = (jobId) => `${API_V1}/analyses/${jobId}/video`;

export const fetchPoseData = async (jobId) => {
  const res = await fetch(`${API_V1}/analyses/${jobId}/pose`);
  if (!res.ok) return null;
  return await res.json();
};

// Legacy support
export const fetchSessions = async () => {
  try {
    const res = await fetch(`${API_BASE}/sessions`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.sessions || [];
  } catch (e) {
    return [];
  }
};

export const fetchResults = async (sessionId) => {
  const res = await fetch(`${API_BASE}/results/${sessionId}`);
  if (!res.ok) throw new Error(`Session '${sessionId}' results not found`);
  return await res.json();
};
