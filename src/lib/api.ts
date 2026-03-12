const API_BASE = "http://localhost:8000/api";

let authToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  authToken = token;
};

const headers = (extra?: Record<string, string>) => {
  const h: Record<string, string> = { "Content-Type": "application/json", ...extra };
  if (authToken) h["Authorization"] = `Bearer ${authToken}`;
  return h;
};

export const api = {
  getLeads: () => fetch(`${API_BASE}/leads`, { headers: headers() }).then(r => r.json()),
  captureLead: (text: string) => fetch(`${API_BASE}/leads/capture`, { method: "POST", headers: headers(), body: JSON.stringify({ text }) }).then(r => r.json()),
  getContracts: () => fetch(`${API_BASE}/contracts`, { headers: headers() }).then(r => r.json()),
  generateContract: (leadId: string) => fetch(`${API_BASE}/contracts/generate`, { method: "POST", headers: headers(), body: JSON.stringify({ lead_id: leadId }) }).then(r => r.json()),
  editContract: (id: string, data: any) => fetch(`${API_BASE}/contracts/${id}`, { method: "PATCH", headers: headers(), body: JSON.stringify(data) }).then(r => r.json()),
  sendForSigning: (id: string) => fetch(`${API_BASE}/contracts/${id}/send-for-signing`, { method: "POST", headers: headers() }).then(r => r.json()),
  getInvoices: () => fetch(`${API_BASE}/invoices`, { headers: headers() }).then(r => r.json()),
  sendInvoice: (id: string) => fetch(`${API_BASE}/invoices/${id}/send`, { method: "POST", headers: headers() }).then(r => r.json()),
  chat: (message: string, sessionId: string) => fetch(`${API_BASE}/chat`, { method: "POST", headers: headers(), body: JSON.stringify({ message, session_id: sessionId }) }),
  getChatHistory: (sessionId: string) => fetch(`${API_BASE}/chat/history/${sessionId}`, { headers: headers() }).then(r => r.json()),
  executeChatAction: (action: any) => fetch(`${API_BASE}/chat/action`, { method: "POST", headers: headers(), body: JSON.stringify(action) }).then(r => r.json()),
  signContract: (token: string, data: { name: string }) => fetch(`${API_BASE}/contracts/sign/${token}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }).then(r => r.json()),
};
