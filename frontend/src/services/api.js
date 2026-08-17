const API_BASE = '/api';

export const fetchSports = async () => {
  const res = await fetch(`${API_BASE}/sports`);
  if (!res.ok) throw new Error('Failed to fetch registered sports');
  const data = await res.json();
  return data.sports;
};

export const fetchSportDetail = async (sportName) => {
  const res = await fetch(`${API_BASE}/sports/${sportName}`);
  if (!res.ok) throw new Error(`Sport '${sportName}' detail not found`);
  return await res.json();
};

export const analyzeVideo = async (sportName, file) => {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/analyze/${sportName}`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Video analysis failed');
  }

  return await res.json();
};

export const fetchSessions = async () => {
  const res = await fetch(`${API_BASE}/sessions`);
  if (!res.ok) throw new Error('Failed to fetch session history');
  const data = await res.json();
  return data.sessions;
};

export const fetchResults = async (sessionId) => {
  const res = await fetch(`${API_BASE}/results/${sessionId}`);
  if (!res.ok) throw new Error(`Session '${sessionId}' results not found`);
  return await res.json();
};
