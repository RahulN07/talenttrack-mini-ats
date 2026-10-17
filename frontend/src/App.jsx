
import { useEffect, useCallback, useState } from "react";
import {
  Users,
  UserPlus,
  Search,
  BriefcaseBusiness,
  Clock3,
  CheckCircle2,
  RefreshCw,
  Trash2,
  LayoutDashboard,
  ArrowUpRight,
} from "lucide-react";
import "./App.css";

const API = "http://127.0.0.1:8000";

const STAGES = [
  "Applied",
  "Screening",
  "Interviewing",
  "Offer",
  "Hired",
  "Rejected",
];

const EMPTY_FORM = {
  name: "",
  email: "",
  role: "",
  stage: "Applied",
};

function App() {
  const [candidates, setCandidates] = useState([]);
  const [metrics, setMetrics] = useState({
    total_candidates: 0,
    stage_counts: {},
  });
  const [search, setSearch] = useState("");
  const [stageFilter, setStageFilter] = useState("");
  const [form, setForm] = useState(EMPTY_FORM);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams();
      if (search.trim()) params.set("search", search.trim());
      if (stageFilter) params.set("stage", stageFilter);

      const [candidateResponse, dashboardResponse] = await Promise.all([
        fetch(`${API}/candidates?${params.toString()}`),
        fetch(`${API}/dashboard`),
      ]);

      if (!candidateResponse.ok || !dashboardResponse.ok) {
        throw new Error("The API returned an error. Please try refreshing.");
      }

      const candidateData = await candidateResponse.json();
      const dashboardData = await dashboardResponse.json();

      setCandidates(candidateData);
      setMetrics(dashboardData);
    } catch {
      setError(
        "Cannot connect to the backend. Check that FastAPI is running at " +
          API +
          ".",
      );
    } finally {
      setLoading(false);
    }
  }, [search, stageFilter]);

  useEffect(() => {
  const timer = setTimeout(() => {
    loadData();
  }, 0);

  return () => clearTimeout(timer);
  }, [loadData]);

  async function addCandidate(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");

    try {
      const response = await fetch(`${API}/candidates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail
            ? typeof data.detail === "string"
              ? data.detail
              : JSON.stringify(data.detail)
            : "Could not add candidate.",
        );
      }

      setForm(EMPTY_FORM);
      setShowForm(false);
      setSearch("");
      setStageFilter("");
      setNotice("Candidate added successfully.");
      await loadData();
    } catch (err) {
      setError(err.message || "Could not add candidate.");
    } finally {
      setSaving(false);
    }
  }

  async function updateStage(candidate, newStage) {
    if (newStage === candidate.stage) return;

    setError("");
    setNotice("");

    try {
      const response = await fetch(
        `${API}/candidates/${candidate.id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: candidate.name,
            email: candidate.email,
            role: candidate.role,
            stage: newStage,
          }),
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not update hiring stage.");
      }

      setNotice(`${candidate.name}'s stage updated.`);
      await loadData();
    } catch (err) {
      setError(err.message || "Could not update hiring stage.");
    }
  }

  async function deleteCandidate(candidate) {
    const confirmed = window.confirm(
      `Delete ${candidate.name} from the candidate list?`,
    );

    if (!confirmed) return;

    setError("");
    setNotice("");

    try {
      const response = await fetch(
        `${API}/candidates/${candidate.id}`,
        { method: "DELETE" },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not delete candidate.");
      }

      setNotice("Candidate deleted.");
      await loadData();
    } catch (err) {
      setError(err.message || "Could not delete candidate.");
    }
  }

  const stageCount = (stage) => metrics.stage_counts?.[stage] ?? 0;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#dashboard">
          <span className="brand-mark">T</span>
          <span>TalentTrack</span>
        </a>

        <div className="sidebar-label">WORKSPACE</div>
        <a className="nav-item active" href="#dashboard">
          <LayoutDashboard size={18} />
          Dashboard
        </a>
        <a className="nav-item" href="#candidates">
          <Users size={18} />
          Candidates
        </a>

        <div className="sidebar-bottom">
          <div className="avatar">RN</div>
          <div>
            <strong>Recruiter workspace</strong>
            <span>Mini ATS · Demo</span>
          </div>
        </div>
      </aside>

      <main className="main-content" id="dashboard">
        <header className="topbar">
          <div>
            <div className="eyebrow">RECRUITMENT WORKSPACE</div>
            <h1>Dashboard</h1>
            <p className="subtitle">
              Track candidates and keep your hiring process moving.
            </p>
          </div>
          <button
            className="primary-button"
            onClick={() => {
              setShowForm(!showForm);
              setError("");
              setNotice("");
            }}
          >
            <UserPlus size={18} />
            Add candidate
          </button>
        </header>

        {error && (
          <div className="message error-message" role="alert">
            {error}
          </div>
        )}
        {notice && (
          <div className="message success-message" role="status">
            {notice}
          </div>
        )}

        {showForm && (
          <section className="panel form-panel">
            <div className="section-heading">
              <div>
                <h2>Add a candidate</h2>
                <p>Enter the candidate's basic information.</p>
              </div>
              <button
                className="text-button"
                onClick={() => setShowForm(false)}
              >
                Cancel
              </button>
            </div>

            <form className="candidate-form" onSubmit={addCandidate}>
              <label>
                Full name
                <input
                  required
                  minLength={2}
                  value={form.name}
                  onChange={(e) =>
                    setForm({ ...form, name: e.target.value })
                  }
                  placeholder="e.g. Aarav Sharma"
                />
              </label>
              <label>
                Email address
                <input
                  required
                  type="email"
                  value={form.email}
                  onChange={(e) =>
                    setForm({ ...form, email: e.target.value })
                  }
                  placeholder="aarav@example.com"
                />
              </label>
              <label>
                Position
                <input
                  required
                  value={form.role}
                  onChange={(e) =>
                    setForm({ ...form, role: e.target.value })
                  }
                  placeholder="e.g. Python Developer"
                />
              </label>
              <label>
                Hiring stage
                <select
                  value={form.stage}
                  onChange={(e) =>
                    setForm({ ...form, stage: e.target.value })
                  }
                >
                  {STAGES.map((stage) => (
                    <option key={stage} value={stage}>
                      {stage}
                    </option>
                  ))}
                </select>
              </label>
              <div className="form-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setForm(EMPTY_FORM)}
                >
                  Clear
                </button>
                <button
                  className="primary-button"
                  type="submit"
                  disabled={saving}
                >
                  {saving ? "Saving..." : "Save candidate"}
                </button>
              </div>
            </form>
          </section>
        )}

        <section className="metrics-grid" aria-label="Hiring metrics">
          <MetricCard
            icon={<Users size={20} />}
            label="Total candidates"
            value={metrics.total_candidates ?? 0}
            detail="All candidate records"
            tone="blue"
          />
          <MetricCard
            icon={<Clock3 size={20} />}
            label="In screening"
            value={stageCount("Screening")}
            detail="Under initial review"
            tone="amber"
          />
          <MetricCard
            icon={<BriefcaseBusiness size={20} />}
            label="Interviewing"
            value={stageCount("Interviewing")}
            detail="In the interview stage"
            tone="purple"
          />
          <MetricCard
            icon={<CheckCircle2 size={20} />}
            label="Hired"
            value={stageCount("Hired")}
            detail="Successfully hired"
            tone="green"
          />
        </section>

        <section className="pipeline-section">
          <div className="section-heading">
            <div>
              <h2>Hiring pipeline</h2>
              <p>Candidate distribution across each stage.</p>
            </div>
          </div>
          <div className="pipeline-grid">
            {STAGES.map((stage) => {
              const count = stageCount(stage);
              const total = metrics.total_candidates || 0;
              const percentage =
                total > 0 ? Math.round((count / total) * 100) : 0;

              return (
                <button
                  key={stage}
                  className="pipeline-card"
                  onClick={() =>
                    setStageFilter(stageFilter === stage ? "" : stage)
                  }
                  title={`Filter candidates in ${stage}`}
                >
                  <div className="pipeline-card-top">
                    <span className={`stage-dot dot-${stage.toLowerCase()}`} />
                    <span>{stage}</span>
                    <ArrowUpRight size={15} />
                  </div>
                  <strong>{count}</strong>
                  <div className="progress-track">
                    <div
                      className={`progress-fill fill-${stage.toLowerCase()}`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="pipeline-percent">{percentage}% of candidates</span>
                </button>
              );
            })}
          </div>
        </section>

        <section className="panel candidates-panel" id="candidates">
          <div className="section-heading candidates-heading">
            <div>
              <h2>Candidates</h2>
              <p>Search, review, and manage your applicants.</p>
            </div>
            <button className="icon-button" onClick={loadData} title="Refresh">
              <RefreshCw size={17} />
            </button>
          </div>

          <div className="toolbar">
            <div className="search-box">
              <Search size={18} />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search name, email, or role..."
                aria-label="Search candidates"
              />
            </div>
            <select
              className="filter-select"
              value={stageFilter}
              onChange={(e) => setStageFilter(e.target.value)}
              aria-label="Filter by hiring stage"
            >
              <option value="">All stages</option>
              {STAGES.map((stage) => (
                <option key={stage} value={stage}>
                  {stage}
                </option>
              ))}
            </select>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Position</th>
                  <th>Hiring stage</th>
                  <th className="actions-heading">Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="4" className="empty-state">
                      Loading candidates...
                    </td>
                  </tr>
                ) : candidates.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="empty-state">
                      <div className="empty-icon">
                        <Users size={24} />
                      </div>
                      <strong>No candidates found</strong>
                      <span>
                        Add a candidate or change your search filters.
                      </span>
                    </td>
                  </tr>
                ) : (
                  candidates.map((candidate) => (
                    <tr key={candidate.id}>
                      <td>
                        <div className="candidate-cell">
                          <div className="candidate-avatar">
                            {candidate.name
                              .split(/\s+/)
                              .map((part) => part[0])
                              .join("")
                              .slice(0, 2)
                              .toUpperCase()}
                          </div>
                          <div className="candidate-details">
                            <strong>{candidate.name}</strong>
                            <span>{candidate.email}</span>
                          </div>
                        </div>
                      </td>
                      <td>{candidate.role}</td>
                      <td>
                        <select
                          className={`stage-select stage-${candidate.stage.toLowerCase()}`}
                          value={candidate.stage}
                          onChange={(e) =>
                            updateStage(candidate, e.target.value)
                          }
                          aria-label={`Change stage for ${candidate.name}`}
                        >
                          {STAGES.map((stage) => (
                            <option key={stage} value={stage}>
                              {stage}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="actions-cell">
                        <button
                          className="delete-button"
                          title={`Delete ${candidate.name}`}
                          aria-label={`Delete ${candidate.name}`}
                          onClick={() => deleteCandidate(candidate)}
                        >
                          <Trash2 size={17} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <footer className="table-footer">
            <span>
              Showing {candidates.length} candidate
              {candidates.length === 1 ? "" : "s"}
              {stageFilter ? ` · ${stageFilter}` : ""}
            </span>
            <span className="api-status">
              <span className="status-dot" /> Connected to API
            </span>
          </footer>
        </section>

        <footer className="page-footer">
          TalentTrack Mini ATS <span>·</span> Built for EarlyJobs.ai screening
        </footer>
      </main>
    </div>
  );
}

function MetricCard({ icon, label, value, detail, tone }) {
  return (
    <article className="metric-card">
      <div className={`metric-icon ${tone}`}>{icon}</div>
      <span className="metric-label">{label}</span>
      <strong className="metric-value">{value}</strong>
      <span className="metric-detail">{detail}</span>
    </article>
  );
}

export default App;
