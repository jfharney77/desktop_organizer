import { useState } from "react";
import styles from "./App.module.css";

const API_BASE = "http://localhost:8000";

const TABS = [
  {
    key:      "images",
    label:    "Images",
    endpoint: "/organize",
    subtitle: "Move or copy PNG/JPEG images from a source directory to a destination.",
    ignoredLogLabel: "Ignored Images Log",
    movedLogLabel:   "Moved Images Log",
  },
  {
    key:      "powerpoint",
    label:    "PowerPoint",
    endpoint: "/organize/pptx",
    subtitle: "Move or copy .pptx/.ppt files from a source directory to a destination.",
    ignoredLogLabel: "Ignored Files Log",
    movedLogLabel:   "Moved Files Log",
  },
  {
    key:      "txt",
    label:    "Text Files",
    endpoint: "/organize/txt",
    subtitle: "Move or copy .txt files from a source directory to a destination.",
    ignoredLogLabel: "Ignored Files Log",
    movedLogLabel:   "Moved Files Log",
  },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function buildCurlCommand(endpoint, body) {
  const lines = [
    `curl -X POST ${API_BASE}${endpoint} \\`,
    `  -H "Content-Type: application/json" \\`,
    `  -d '${JSON.stringify(body, null, 2)}'`,
  ];
  return lines.join("\n");
}

// ---------------------------------------------------------------------------
// Shared sub-components
// ---------------------------------------------------------------------------

function Field({ label, id, value, onChange, placeholder }) {
  return (
    <div className={styles.field}>
      <label htmlFor={id}>{label}</label>
      <input
        type="text"
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoComplete="off"
        spellCheck={false}
      />
    </div>
  );
}

function Result({ state }) {
  if (!state) return null;
  const cls = state.type === "success" ? styles.resultSuccess : styles.resultError;
  return (
    <div className={cls}>
      <div className={styles.resultLabel}>{state.label}</div>
      <pre className={styles.resultText}>{state.text}</pre>
    </div>
  );
}

function CliCommand({ command }) {
  if (!command) return null;
  const [copied, setCopied] = useState(false);

  function copy() {
    navigator.clipboard.writeText(command).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <details className={styles.cliDetails}>
      <summary className={styles.cliSummary}>Equivalent curl command</summary>
      <div className={styles.cliBody}>
        <pre className={styles.cliCode}>{command}</pre>
        <button className={styles.copyBtn} onClick={copy}>
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
    </details>
  );
}

// ---------------------------------------------------------------------------
// Organizer panel — reused for every tab
// ---------------------------------------------------------------------------

function OrganizerPanel({ tab }) {
  const [source, setSource]         = useState("");
  const [dest, setDest]             = useState("");
  const [retainCopy, setRetainCopy] = useState(false);
  const [ignoredLog, setIgnoredLog] = useState("");
  const [movedLog, setMovedLog]     = useState("");
  const [loading, setLoading]       = useState(false);
  const [result, setResult]         = useState(null);
  const [cliCommand, setCliCommand] = useState(null);

  async function runOrganize() {
    if (!source.trim() || !dest.trim()) {
      setResult({ type: "error", label: "Error", text: "Source and destination directories are required." });
      setCliCommand(null);
      return;
    }

    const body = {
      source_directory:      source.trim(),
      destination_directory: dest.trim(),
      retain_copy:           retainCopy,
    };
    if (ignoredLog.trim()) body.ignored_log = ignoredLog.trim();
    if (movedLog.trim())   body.moved_log   = movedLog.trim();

    setCliCommand(buildCurlCommand(tab.endpoint, body));
    setLoading(true);
    setResult(null);

    try {
      const res  = await fetch(`${API_BASE}${tab.endpoint}`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(body),
      });

      const data = await res.json();

      if (!res.ok) {
        setResult({ type: "error", label: "Server Error", text: data.detail ?? JSON.stringify(data, null, 2) });
        return;
      }

      const summary = [
        `Source:        ${data.source_directory}`,
        `Destination:   ${data.destination_directory}`,
        `Copy retained: ${data.retain_copy ? "Yes" : "No"}`,
        "",
        data.agent_summary,
      ].join("\n");

      setResult({ type: "success", label: "Complete", text: summary });

    } catch {
      setResult({
        type:  "error",
        label: "Connection Error",
        text:  `Could not reach the API at ${API_BASE}.\n\nMake sure the server is running:\n  bash script/bash/run_uv.sh`,
      });
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !loading) runOrganize();
  }

  return (
    <div onKeyDown={handleKeyDown}>
      <p className={styles.subtitle}>{tab.subtitle}</p>

      <Field label="Source Directory"      id={`${tab.key}-source`} value={source} onChange={setSource} placeholder="/path/to/source" />
      <Field label="Destination Directory" id={`${tab.key}-dest`}   value={dest}   onChange={setDest}   placeholder="/path/to/destination" />

      <div className={styles.toggleRow}>
        <label className={styles.toggle}>
          <input type="checkbox" checked={retainCopy} onChange={(e) => setRetainCopy(e.target.checked)} />
          <span className={styles.slider} />
        </label>
        <span className={styles.toggleLabel}>Retain copy in source directory</span>
      </div>

      <hr className={styles.divider} />

      <details>
        <summary className={styles.advancedSummary}>Advanced — log file paths</summary>
        <div className={styles.advancedBody}>
          <Field label={tab.ignoredLogLabel} id={`${tab.key}-ignoredLog`} value={ignoredLog} onChange={setIgnoredLog} placeholder="Leave blank to use config.yaml default" />
          <Field label={tab.movedLogLabel}   id={`${tab.key}-movedLog`}   value={movedLog}   onChange={setMovedLog}   placeholder="Leave blank to use config.yaml default" />
        </div>
      </details>

      <button className={styles.btn} onClick={runOrganize} disabled={loading}>
        {loading ? "Running…" : "Run Organizer"}
      </button>

      <Result state={result} />
      <CliCommand command={cliCommand} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Root
// ---------------------------------------------------------------------------

export default function App() {
  const [activeTab, setActiveTab] = useState(TABS[0].key);
  const tab = TABS.find((t) => t.key === activeTab);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.pageTitle}>Desktop Organizer</h1>
      </header>

      <div className={styles.card}>
        <nav className={styles.tabs}>
          {TABS.map((t) => (
            <button
              key={t.key}
              className={`${styles.tab} ${activeTab === t.key ? styles.tabActive : ""}`}
              onClick={() => setActiveTab(t.key)}
            >
              {t.label}
            </button>
          ))}
        </nav>

        <div className={styles.tabContent}>
          <OrganizerPanel key={activeTab} tab={tab} />
        </div>
      </div>
    </div>
  );
}
