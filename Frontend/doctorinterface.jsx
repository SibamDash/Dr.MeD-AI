const { useState, useEffect, useCallback } = React;

// ─── Constants ────────────────────────────────────────────────────────────────
const STATUS_CONFIG = {
  PENDING:  { bg: 'bg-amber-100',   text: 'text-amber-800',   label: 'Pending',  icon: '⏳' },
  VERIFIED: { bg: 'bg-emerald-100', text: 'text-emerald-800', label: 'Verified', icon: '✓' },
  REJECTED: { bg: 'bg-red-100',     text: 'text-red-800',     label: 'Rejected', icon: '✗' },
};

const PRIORITY_CONFIG = {
  HIGH:   { bg: 'bg-red-100',    text: 'text-red-800',    label: 'High' },
  MEDIUM: { bg: 'bg-orange-100', text: 'text-orange-800', label: 'Medium' },
  LOW:    { bg: 'bg-sky-100',    text: 'text-sky-800',    label: 'Low' },
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
const formatTimestamp = (ts) =>
  new Date(ts).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

const confidenceColor = (v) =>
  v >= 90 ? 'text-emerald-600' : v >= 75 ? 'text-amber-600' : 'text-red-600';

const confidenceBg = (v) =>
  v >= 90 ? 'bg-emerald-500' : v >= 75 ? 'bg-amber-500' : 'bg-red-500';

// ─── Sub-components ───────────────────────────────────────────────────────────

/** Accessible modal overlay – closes on Escape or backdrop click */
const Modal = ({ open, onClose, children }) => {
  useEffect(() => {
    if (!open) return;
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        {children}
      </div>
    </div>
  );
};

/** Auto-dismissing toast notification */
const Toast = ({ message, type, onDismiss }) => {
  useEffect(() => {
    const t = setTimeout(onDismiss, 3500);
    return () => clearTimeout(t);
  }, [onDismiss]);

  const colorMap = { success: 'bg-emerald-600', error: 'bg-red-600', info: 'bg-[#1E3A8A]' };
  const iconMap  = { success: '✓', error: '✗', info: 'ℹ' };

  return (
    <div
      className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3 rounded-xl text-white shadow-2xl text-sm font-medium ${colorMap[type]}`}
      role="status"
    >
      <span>{iconMap[type]}</span>
      {message}
      <button onClick={onDismiss} className="ml-2 opacity-70 hover:opacity-100 text-lg leading-none">×</button>
    </div>
  );
};

const StatusBadge = ({ status }) => {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.PENDING;
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${cfg.bg} ${cfg.text}`}>
      {cfg.icon} {cfg.label}
    </span>
  );
};

const PriorityBadge = ({ priority }) => {
  const cfg = PRIORITY_CONFIG[priority] ?? PRIORITY_CONFIG.MEDIUM;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${cfg.bg} ${cfg.text}`}>
      {cfg.label}
    </span>
  );
};

const StatCard = ({ label, value, color, highlighted }) => (
  <div className={`bg-white rounded-xl shadow-sm p-4 border-2 ${highlighted ? 'border-red-200' : 'border-transparent'}`}>
    <div className={`text-2xl font-extrabold ${color}`}>{value}</div>
    <div className="text-xs text-gray-500 mt-0.5">{label}</div>
  </div>
);

// ─── Main Component ───────────────────────────────────────────────────────────
const DoctorInterface = ({ user }) => {
  const [reports, setReports]                     = useState([]);
  const [selectedReport, setSelectedReport]       = useState(null);
  const [editedExplanation, setEditedExplanation] = useState('');
  const [loading, setLoading]                     = useState(false);
  const [filterStatus, setFilterStatus]           = useState('all');
  const [filterPriority, setFilterPriority]       = useState('all');
  const [searchQuery, setSearchQuery]             = useState('');

  // Modal flags
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [showRejectModal, setShowRejectModal]   = useState(false);
  const [showSaveModal, setShowSaveModal]       = useState(false);
  const [rejectReason, setRejectReason]         = useState('');

  // Toast
  const [toast, setToast] = useState(null);
  const showToast = useCallback((message, type = 'info') => setToast({ message, type }), []);

  // ── Data Fetching ──────────────────────────────────────────────────────────
  const fetchReports = useCallback(async () => {
    if (!user || !user.uid) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/doctor/inbox/${user.uid}`);
      const data = await res.json();
      if (data.success) {
        const transformedReports = data.reports.map(report => {
          const analysisResult = report.result || report;
          const patientContext = analysisResult.patientContext || {};
          const aiResponse = analysisResult.aiResponse || {};
          return {
            id: analysisResult.analysisId,
            patientId: patientContext.uid || 'N/A',
            patientName: patientContext.name || 'Unknown Patient',
            age: patientContext.age || 'N/A',
            timestamp: analysisResult.processedAt || new Date().toISOString(),
            medicalCondition: patientContext.condition || 'N/A',
            aiConfidence: analysisResult.confidence || 0,
            status: report.verificationStatus || 'PENDING', // Use saved status
            priority: 'HIGH', // Default priority
            findings: analysisResult.findings || [],
            aiExplanation: aiResponse.clinical_interpretation || analysisResult.analysis || 'No summary.',
            recommendations: (analysisResult.recommendations || []).map(r => `${r.title}: ${r.description}`),
            uncertainties: analysisResult.uncertainties || [],
          };
        });
        setReports(transformedReports);
      } else { throw new Error(data.error); }
    } catch (err) {
      console.error('Failed to fetch reports:', err);
      showToast('Failed to load reports', 'error');
    } finally {
      setLoading(false);
    }
  }, [user, showToast]);

  useEffect(() => {
    if (user) {
      fetchReports();
      const intervalId = setInterval(fetchReports, 30000); // Refresh every 30 seconds
      return () => clearInterval(intervalId); // Cleanup on unmount
    }
  }, [user, fetchReports]);

  // ── Actions ────────────────────────────────────────────────────────────────

  const handleApproveConfirm = async () => {
    if (!selectedReport) return;
    setShowApproveModal(false);
    try {
      await fetch(`/api/doctor/inbox/${user.uid}/${selectedReport.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'VERIFIED' })
      });
      const updated = { ...selectedReport, status: 'VERIFIED' };
      setReports((prev) => prev.map((r) => (r.id === selectedReport.id ? updated : r)));
      setSelectedReport(updated);
      showToast('Report approved successfully', 'success');
    } catch (err) {
      console.error(err);
      showToast('Failed to approve report', 'error');
    }
  };

  const handleRejectConfirm = async () => {
    if (!selectedReport || !rejectReason.trim()) return;
    setShowRejectModal(false);
    try {
      await fetch(`/api/doctor/inbox/${user.uid}/${selectedReport.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'REJECTED', reason: rejectReason })
      });
      const updated = { ...selectedReport, status: 'REJECTED', rejectionReason: rejectReason };
      setReports((prev) => prev.map((r) => (r.id === selectedReport.id ? updated : r)));
      setSelectedReport(updated);
      setRejectReason('');
      showToast('Report rejected', 'error');
    } catch (err) {
      console.error(err);
      showToast('Failed to reject report', 'error');
    }
  };

  const handleSaveConfirm = async () => {
    if (!selectedReport || !editedExplanation.trim()) return;
    setShowSaveModal(false);
    try {
      await fetch(`/api/doctor/inbox/${user.uid}/${selectedReport.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ aiExplanation: editedExplanation })
      });
      const updated = { ...selectedReport, aiExplanation: editedExplanation };
      setReports((prev) => prev.map((r) => (r.id === selectedReport.id ? updated : r)));
      setSelectedReport(updated);
      showToast('Changes saved successfully', 'success');
    } catch (err) {
      console.error(err);
      showToast('Failed to save changes', 'error');
    }
  };

  const handleReportClick = (report) => {
    setSelectedReport(report);
    setEditedExplanation(report.aiExplanation);
  };

  const handleClosePanel = () => {
    setSelectedReport(null);
    setEditedExplanation('');
  };

  // ── Filtering ──────────────────────────────────────────────────────────────
  const filteredReports = reports.filter((r) => {
    const q = searchQuery.toLowerCase();
    return (
      (filterStatus === 'all'   || r.status   === filterStatus)   &&
      (filterPriority === 'all' || r.priority === filterPriority) &&
      (
        r.patientId.toLowerCase().includes(q)       ||
        r.patientName.toLowerCase().includes(q)     ||
        r.medicalCondition.toLowerCase().includes(q)
      )
    );
  });

  // ── Stats ──────────────────────────────────────────────────────────────────
  const stats = {
    total:        reports.length,
    pending:      reports.filter((r) => r.status === 'PENDING').length,
    verified:     reports.filter((r) => r.status === 'VERIFIED').length,
    rejected:     reports.filter((r) => r.status === 'REJECTED').length,
    highPriority: reports.filter((r) => r.priority === 'HIGH' && r.status === 'PENDING').length,
  };

  // Whether the explanation textarea has unsaved changes
  const isDirty = selectedReport != null && editedExplanation !== selectedReport.aiExplanation;

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-50">

      {/* Toast */}
      {toast && <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} />}

      {/* ── Approve Modal ── */}
      <Modal open={showApproveModal} onClose={() => setShowApproveModal(false)}>
        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 font-bold text-lg">✓</div>
            <h2 className="text-lg font-bold text-gray-900">Approve Report</h2>
          </div>
          <p className="text-sm text-gray-600 mb-6">
            Are you sure you want to approve the report for{' '}
            <strong>{selectedReport?.patientName}</strong>? This will mark it as verified.
          </p>
          <div className="flex gap-3 justify-end">
            <button
              onClick={() => setShowApproveModal(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleApproveConfirm}
              className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
            >
              Confirm Approval
            </button>
          </div>
        </div>
      </Modal>

      {/* ── Reject Modal ── */}
      <Modal open={showRejectModal} onClose={() => { setShowRejectModal(false); setRejectReason(''); }}>
        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center text-red-600 font-bold text-lg">✗</div>
            <h2 className="text-lg font-bold text-gray-900">Reject Report</h2>
          </div>
          <p className="text-sm text-gray-600 mb-3">
            Please provide a reason for rejecting <strong>{selectedReport?.patientName}</strong>'s report.
          </p>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={4}
            placeholder="Enter rejection reason…"
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-red-400 focus:border-transparent mb-4"
          />
          <div className="flex gap-3 justify-end">
            <button
              onClick={() => { setShowRejectModal(false); setRejectReason(''); }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleRejectConfirm}
              disabled={!rejectReason.trim()}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Confirm Rejection
            </button>
          </div>
        </div>
      </Modal>

      {/* ── Save Modal ── */}
      <Modal open={showSaveModal} onClose={() => setShowSaveModal(false)}>
        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-[#1E3A8A] text-lg">💾</div>
            <h2 className="text-lg font-bold text-gray-900">Save Changes</h2>
          </div>
          <p className="text-sm text-gray-600 mb-6">
            Save your edits to the AI explanation for <strong>{selectedReport?.patientName}</strong>?
          </p>
          <div className="flex gap-3 justify-end">
            <button
              onClick={() => setShowSaveModal(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveConfirm}
              className="px-4 py-2 text-sm font-medium text-white bg-[#1E3A8A] rounded-lg hover:bg-blue-900 transition-colors"
            >
              Save Edits
            </button>
          </div>
        </div>
      </Modal>

      {/* ── Page ── */}
      <div className="max-w-7xl mx-auto px-6 py-8">

        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-3xl font-extrabold text-[#1E3A8A] tracking-tight mb-1">
              Doctor Verification Panel
            </h1>
            <p className="text-gray-500 text-sm">Review and verify AI-generated medical reports</p>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="/medical-ai.html"
              className="flex items-center gap-2 text-sm font-medium text-white bg-[#1E3A8A] rounded-lg px-4 py-2 hover:bg-blue-900 shadow-sm transition-colors"
            >
              🏠 Home
            </a>
            <button
              onClick={fetchReports}
              className="flex items-center gap-2 text-sm font-medium text-[#1E3A8A] bg-white border border-gray-200 rounded-lg px-4 py-2 hover:bg-gray-50 shadow-sm transition-colors"
            >
              🔄 Refresh
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
          <StatCard label="Total Reports"   value={stats.total}        color="text-[#1E3A8A]" />
          <StatCard label="Pending Review"  value={stats.pending}      color="text-amber-600" />
          <StatCard label="Verified"        value={stats.verified}     color="text-emerald-600" />
          <StatCard label="Rejected"        value={stats.rejected}     color="text-red-600" />
          <StatCard label="High Priority"   value={stats.highPriority} color="text-red-600" highlighted />
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <input
              type="text"
              placeholder="Search by patient, ID, or condition…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="sm:col-span-2 px-4 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent"
            />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="PENDING">Pending</option>
              <option value="VERIFIED">Verified</option>
              <option value="REJECTED">Rejected</option>
            </select>
            <select
              value={filterPriority}
              onChange={(e) => setFilterPriority(e.target.value)}
              className="px-4 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent"
            >
              <option value="all">All Priority</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

          {/* ── Report List ── */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
                <h2 className="font-bold text-gray-800">Reports Queue</h2>
                <span className="text-xs font-semibold text-white bg-[#1E3A8A] rounded-full px-2 py-0.5">
                  {filteredReports.length}
                </span>
              </div>

              {loading ? (
                <div className="flex flex-col items-center justify-center py-16 text-gray-400 text-sm">
                  <div className="w-8 h-8 border-2 border-[#1E3A8A] border-t-transparent rounded-full animate-spin mb-3" />
                  Loading reports…
                </div>
              ) : filteredReports.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-gray-400 text-sm">
                  <span className="text-4xl mb-3">📄</span>
                  No reports match your filters
                </div>
              ) : (
                <div className="divide-y divide-gray-50 max-h-[70vh] overflow-y-auto">
                  {filteredReports.map((report) => {
                    const isSelected = selectedReport?.id === report.id;
                    return (
                      <button
                        key={report.id}
                        onClick={() => handleReportClick(report)}
                        className={`w-full text-left px-5 py-4 transition-colors border-l-4 ${
                          isSelected
                            ? 'border-[#1E3A8A] bg-blue-50'
                            : 'border-transparent hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <div>
                            <span className="font-semibold text-gray-900 text-sm">{report.patientName}</span>
                            <span className="ml-2 text-xs text-gray-400">{report.patientId}</span>
                          </div>
                          <div className="flex flex-col items-end gap-1 shrink-0">
                            <StatusBadge status={report.status} />
                            <PriorityBadge priority={report.priority} />
                          </div>
                        </div>
                        <div className="text-xs text-gray-500 mb-2">
                          Age {report.age} · {formatTimestamp(report.timestamp)}
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-600">{report.medicalCondition}</span>
                          <span className={`font-bold ${confidenceColor(report.aiConfidence)}`}>
                            {report.aiConfidence}% AI
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* ── Detail Panel ── */}
          <div className="lg:col-span-3">
            {!selectedReport ? (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center py-28 text-gray-400">
                <span className="text-5xl mb-4">🩺</span>
                <p className="text-sm">Select a report from the queue to begin review</p>
              </div>
            ) : (
              <div className="space-y-4">

                {/* Quick Actions Card */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-bold text-[#1E3A8A]">Quick Actions</h3>
                    <button
                      onClick={handleClosePanel}
                      aria-label="Close detail panel"
                      className="text-gray-400 hover:text-gray-600 transition-colors text-xl leading-none"
                    >
                      ×
                    </button>
                  </div>

                  {/* Patient summary */}
                  <div className="bg-slate-50 rounded-lg p-3 mb-4 grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-xs text-gray-500 block mb-0.5">Patient</span>
                      <span className="font-semibold text-gray-900">{selectedReport.patientName}</span>
                      <span className="text-gray-400 ml-1 text-xs">· Age {selectedReport.age}</span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 block mb-0.5">Condition</span>
                      <span className="font-semibold text-gray-900">{selectedReport.medicalCondition}</span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 block mb-0.5">Status</span>
                      <StatusBadge status={selectedReport.status} />
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 block mb-0.5">Priority</span>
                      <PriorityBadge priority={selectedReport.priority} />
                    </div>
                    <div className="col-span-2">
                      <span className="text-xs text-gray-500 block mb-1">AI Confidence</span>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all ${confidenceBg(selectedReport.aiConfidence)}`}
                            style={{ width: `${selectedReport.aiConfidence}%` }}
                          />
                        </div>
                        <span className={`text-sm font-bold ${confidenceColor(selectedReport.aiConfidence)}`}>
                          {selectedReport.aiConfidence}%
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Action buttons */}
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => setShowApproveModal(true)}
                      disabled={selectedReport.status === 'VERIFIED'}
                      className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      ✓ Approve
                    </button>
                    <button
                      onClick={() => setShowRejectModal(true)}
                      disabled={selectedReport.status === 'REJECTED'}
                      className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-red-600 hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      ✗ Reject
                    </button>
                  </div>
                </div>

                {/* Lab Findings */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                  <h3 className="font-bold text-gray-800 mb-3">Lab Findings</h3>
                  <div className="overflow-x-auto rounded-lg border border-gray-100">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-slate-50">
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Test</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Value</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide hidden sm:table-cell">Normal Range</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50">
                        {selectedReport.findings.map((f, i) => (
                          <tr key={i} className="hover:bg-slate-50 transition-colors">
                            <td className="px-4 py-3 text-gray-700">{f.label}</td>
                            <td className="px-4 py-3 font-semibold text-gray-900">{f.value}</td>
                            <td className="px-4 py-3 text-gray-400 hidden sm:table-cell">{f.normalRange}</td>
                            <td className="px-4 py-3">
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
                                f.status === 'normal'
                                  ? 'bg-emerald-100 text-emerald-700'
                                  : 'bg-amber-100 text-amber-700'
                              }`}>
                                {f.status === 'normal' ? '✓ Normal' : '⚠ Abnormal'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Editable AI Explanation */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-bold text-gray-800">AI Explanation</h3>
                    <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                      isDirty ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-500'
                    }`}>
                      {isDirty ? '● Unsaved changes' : 'Editable'}
                    </span>
                  </div>
                  <textarea
                    value={editedExplanation}
                    onChange={(e) => setEditedExplanation(e.target.value)}
                    rows={5}
                    className="w-full px-4 py-3 text-sm border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent"
                    placeholder="Edit the AI-generated explanation…"
                  />
                  <div className="flex justify-end mt-2">
                    <button
                      onClick={() => {
                        if (!editedExplanation.trim()) {
                          showToast('Explanation cannot be empty', 'error');
                          return;
                        }
                        setShowSaveModal(true);
                      }}
                      disabled={!isDirty}
                      className="px-4 py-2 text-sm font-semibold text-white bg-[#1E3A8A] rounded-lg hover:bg-blue-900 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      💾 Save Edits
                    </button>
                  </div>
                </div>

                {/* Recommendations */}
                {selectedReport.recommendations.length > 0 && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                    <h3 className="font-bold text-gray-800 mb-3">Recommendations</h3>
                    <ul className="space-y-2">
                      {selectedReport.recommendations.map((rec, i) => (
                        <li key={i} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg text-sm text-gray-700">
                          <span className="text-[#1E3A8A] mt-0.5 shrink-0">✔</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Uncertainties */}
                {selectedReport.uncertainties.length > 0 && (
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-5">
                    <h3 className="flex items-center gap-2 text-sm font-bold text-amber-800 mb-3">
                      ⚠ Areas Requiring Attention
                    </h3>
                    <ul className="space-y-2">
                      {selectedReport.uncertainties.map((u, i) => (
                        <li key={i} className="text-sm text-amber-800 flex items-start gap-2">
                          <span className="shrink-0 mt-0.5">•</span>
                          {u}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};