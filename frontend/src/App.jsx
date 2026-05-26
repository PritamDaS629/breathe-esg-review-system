import React from "react";
import { AlertTriangle, Check, Database, FileUp, Filter, Lock, RefreshCw, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const API_BASE = "https://breathe-esg-backend-698mnleyc-pritam-xavi-projects.vercel.app/api";
const sourceLabels = {
  sap: "SAP fuel/procurement",
  utility: "Utility electricity",
  travel: "Corporate travel",
};

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

export default function App() {
  const [bootstrap, setBootstrap] = useState(null);
  const [activities, setActivities] = useState([]);
  const [batches, setBatches] = useState([]);
  const [status, setStatus] = useState("all");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const load = async () => {
  setBusy(true);

  try {
    const [boot, rows, batchRows] = await Promise.all([
      api("/bootstrap/"),
      api(`/activities/?status=${status}`),
      api("/batches/"),
    ]);

    setBootstrap(boot);
    setActivities(rows);
    setBatches(batchRows);

  } catch (error) {
    console.error(error);
    setMessage(error.message);

  } finally {
    setBusy(false);
  }
};

  useEffect(() => {
    load().catch((error) => setMessage(error.message));
  }, [status]);

  const totals = useMemo(() => {
    const flagged = activities.filter((row) => row.flags.length || row.review_status === "flagged").length;
    const locked = activities.filter((row) => row.locked_at).length;
    return { flagged, locked };
  }, [activities]);

  const upload = async (sourceType, file) => {
    if (!file) return;
    const body = new FormData();
    body.append("file", file);
    setBusy(true);
    setMessage("");
    try {
      const batch = await api(`/upload/${sourceType}/`, { method: "POST", body });
      setMessage(`Processed ${batch.filename}: ${batch.accepted_rows} accepted, ${batch.failed_rows} failed.`);
      await load();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  };

  const act = async (id, action) => {
    setBusy(true);
    try {
      await api(`/activities/${id}/${action}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "Analyst decision from dashboard" }),
      });
      await load();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  };

  const counts = bootstrap?.counts || {};

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Breathe ESG</p>
          <h1>Ingestion review</h1>
        </div>
        <button className="iconButton" onClick={load} disabled={busy} title="Refresh data">
          <RefreshCw size={18} />
        </button>
      </header>

      {message && <div className="notice">{message}</div>}

      <section className="metrics">
        <Metric label="Needs review" value={counts.needs_review || 0} icon={<AlertTriangle size={18} />} />
        <Metric label="Approved" value={counts.approved || 0} icon={<Check size={18} />} />
        <Metric label="Locked" value={totals.locked} icon={<Lock size={18} />} />
        <Metric label="Total kg CO2e" value={Number(counts.total_kg_co2e || 0).toLocaleString()} icon={<Database size={18} />} />
      </section>

      <section className="sources">
        {["sap", "utility", "travel"].map((sourceType) => (
          <label className="uploadTile" key={sourceType}>
            <FileUp size={20} />
            <span>{sourceLabels[sourceType]}</span>
            <input type="file" accept=".csv" onChange={(event) => upload(sourceType, event.target.files?.[0])} />
          </label>
        ))}
      </section>

      <section className="reviewBand">
        <div className="sectionTitle">
          <div>
            <p className="eyebrow">Analyst queue</p>
            <h2>Normalized activities</h2>
          </div>
          <label className="filter">
            <Filter size={16} />
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="all">All statuses</option>
              <option value="needs_review">Needs review</option>
              <option value="flagged">Flagged</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </label>
        </div>

        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Source</th>
                <th>Activity</th>
                <th>Scope</th>
                <th>Normalized</th>
                <th>kg CO2e</th>
                <th>Flags</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {activities.map((row) => (
                <tr key={row.id}>
                  <td>{row.activity_date}</td>
                  <td>{row.source.name}</td>
                  <td>
                    <strong>{row.activity_type}</strong>
                    <span>{row.facility?.name || row.source_row_id}</span>
                  </td>
                  <td>{row.scope}</td>
                  <td>{Number(row.normalized_quantity).toLocaleString()} {row.normalized_unit}</td>
                  <td>{Number(row.calculated_kg_co2e).toLocaleString()}</td>
                  <td>
                    {row.flags.length ? row.flags.map((flag) => <em key={flag}>{flag}</em>) : <span className="muted">Clean</span>}
                  </td>
                  <td><Status status={row.review_status} /></td>
                  <td className="actions">
                    <button onClick={() => act(row.id, "approve")} disabled={busy || row.review_status === "approved"} title="Approve and lock">
                      <Check size={16} />
                    </button>
                    <button onClick={() => act(row.id, "reject")} disabled={busy || row.review_status === "rejected"} title="Reject">
                      <X size={16} />
                    </button>
                  </td>
                </tr>
              ))}
              {!activities.length && (
                <tr>
                  <td colSpan="9" className="empty">No rows match this filter.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="batchList">
        <div className="sectionTitle">
          <div>
            <p className="eyebrow">Traceability</p>
            <h2>Recent batches</h2>
          </div>
        </div>
        <div className="batchGrid">
          {batches.map((batch) => (
            <article className="batch" key={batch.id}>
              <strong>{batch.filename}</strong>
              <span>{batch.source.name}</span>
              <p>{batch.accepted_rows}/{batch.total_rows} accepted · {batch.failed_rows} failed</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value, icon }) {
  return (
    <article className="metric">
      <div>{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function Status({ status }) {
  return <span className={`status ${status}`}>{status.replace("_", " ")}</span>;
}
