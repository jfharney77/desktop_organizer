import { useState, useEffect } from "react";
import styles from "./App.module.css";

const API_BASE = "http://localhost:8000";

const TABS = [
  {
    key:             "images",
    label:           "Images",
    endpoint:        "/organize",
    streamEndpoint:  "/organize/stream",
    checkEndpoint:   "/check/images",
    fileLabel:       "image",
    subtitle:        "Move or copy PNG/JPEG images from a source directory to a destination.",
    hint:            "WSL tip: C:\\Users\\jfhar  =  /mnt/c/Users/jfhar",
    ignoredLogLabel: "Ignored Images Log",
    movedLogLabel:   "Moved Images Log",
    fileCheck:       true,
  },
  {
    key:             "powerpoint",
    label:           "PowerPoint",
    endpoint:        "/organize/pptx",
    streamEndpoint:  "/organize/pptx/stream",
    checkEndpoint:   "/check/pptx",
    fileLabel:       "PowerPoint file",
    subtitle:        "Move or copy .pptx/.ppt files from a source directory to a destination.",
    ignoredLogLabel: "Ignored Files Log",
    movedLogLabel:   "Moved Files Log",
    fileCheck:       true,
  },
  {
    key:             "txt",
    label:           "Text Files",
    endpoint:        "/organize/txt",
    streamEndpoint:  "/organize/txt/stream",
    checkEndpoint:   "/check/txt",
    fileLabel:       "text file",
    subtitle:        "Move or copy .txt files from a source directory to a destination.",
    ignoredLogLabel: "Ignored Files Log",
    movedLogLabel:   "Moved Files Log",
    fileCheck:       true,
  },
  {
    key:             "git",
    label:           "Git Repos",
    endpoint:        "/organize/git",
    streamEndpoint:  "/organize/git/stream",
    subtitle:        "Move entire git repositories found inside a source directory to a destination.",
    ignoredLogLabel: "Ignored Repos Log",
    movedLogLabel:   "Moved Repos Log",
    sourceCheck:     true,
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

function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

// ---------------------------------------------------------------------------
// Shared sub-components
// ---------------------------------------------------------------------------

function Field({ label, id, value, onChange, placeholder, badge }) {
  return (
    <div className={styles.field}>
      <div className={styles.fieldLabelRow}>
        <label htmlFor={id}>{label}</label>
        {badge}
      </div>
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

function GitRepoBadge({ path, onReposFound }) {
  const [status, setStatus] = useState(null);
  const debouncedPath = useDebounce(path, 500);

  useEffect(() => {
    if (!debouncedPath.trim()) { setStatus(null); onReposFound([]); return; }
    setStatus("checking");
    fetch(`${API_BASE}/check/git-repo?path=${encodeURIComponent(debouncedPath)}`)
      .then((r) => r.json())
      .then((data) => { setStatus(data); onReposFound(data.repos ?? []); })
      .catch(() => { setStatus(null); onReposFound([]); });
  }, [debouncedPath]);

  if (!status || status === "checking") {
    return status === "checking"
      ? <span className={styles.badgeNeutral}>checking…</span>
      : null;
  }
  if (!status.exists)       return <span className={styles.badgeError}>Directory not found</span>;
  if (status.repo_count === 0) return <span className={styles.badgeWarn}>No git repositories found inside</span>;
  if (status.is_git_repo)   return <span className={styles.badgeWarn}>This directory is itself a git repo — sub-repos scanned inside it</span>;
  return <span className={styles.badgeOk}>{status.repo_count} git repo{status.repo_count !== 1 ? "s" : ""} found</span>;
}

function FileBadge({ path, checkEndpoint, fileLabel, onFilesFound }) {
  const [status, setStatus] = useState(null);
  const debouncedPath = useDebounce(path, 500);

  useEffect(() => {
    if (!debouncedPath.trim()) { setStatus(null); onFilesFound([]); return; }
    setStatus("checking");
    fetch(`${API_BASE}${checkEndpoint}?path=${encodeURIComponent(debouncedPath)}`)
      .then((r) => r.json())
      .then((data) => { setStatus(data); onFilesFound(data.files ?? []); })
      .catch(() => { setStatus(null); onFilesFound([]); });
  }, [debouncedPath]);

  if (!status || status === "checking") {
    return status === "checking"
      ? <span className={styles.badgeNeutral}>checking…</span>
      : null;
  }
  if (!status.exists)          return <span className={styles.badgeError}>Directory not found</span>;
  if (status.file_count === 0) return <span className={styles.badgeWarn}>No {fileLabel}s found</span>;
  return <span className={styles.badgeOk}>{status.file_count} {fileLabel}{status.file_count !== 1 ? "s" : ""} found</span>;
}

function RepoSelector({ repos, selected, onChange, label = "Select all" }) {
  if (!repos || repos.length === 0) return null;

  const allSelected = repos.every((r) => selected.has(r));

  function toggleAll() {
    onChange(allSelected ? new Set() : new Set(repos));
  }

  function toggle(repo) {
    const next = new Set(selected);
    next.has(repo) ? next.delete(repo) : next.add(repo);
    onChange(next);
  }

  return (
    <div className={styles.repoSelector}>
      <div className={styles.repoSelectorHeader}>
        <label className={styles.repoCheckRow}>
          <input type="checkbox" checked={allSelected} onChange={toggleAll} />
          <span className={styles.repoSelectAll}>{label} ({repos.length})</span>
        </label>
        <span className={styles.repoSelectedCount}>
          {selected.size} of {repos.length} selected
        </span>
      </div>
      <ul className={styles.repoList}>
        {repos.map((repo) => {
          const name = repo.split("/").pop() || repo;
          return (
            <li key={repo} className={styles.repoItem}>
              <label className={styles.repoCheckRow} title={repo}>
                <input
                  type="checkbox"
                  checked={selected.has(repo)}
                  onChange={() => toggle(repo)}
                />
                <span className={styles.repoName}>{name}</span>
                <span className={styles.repoPath}>{repo}</span>
              </label>
            </li>
          );
        })}
      </ul>
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

function Progress({ state }) {
  const [open, setOpen] = useState(true);
  if (!state) return null;

  const { percent, current, total, name, scanning } = state;
  const label = scanning
    ? "Scanning…"
    : total === 0
      ? "Nothing to move"
      : `${current ?? 0} / ${total}`;

  return (
    <div className={styles.progressWrap}>
      <div className={styles.progressHeader} onClick={() => setOpen((o) => !o)}>
        <span className={styles.progressTitle}>
          {open ? "▼" : "▶"}&nbsp;&nbsp;Progress — {label}
        </span>
        {!scanning && total > 0 && (
          <span className={styles.progressPct}>{percent ?? 0}%</span>
        )}
      </div>
      {open && (
        <div className={styles.progressBody}>
          <div className={styles.progressTrack}>
            <div
              className={styles.progressBar}
              style={{ width: `${scanning ? 0 : (percent ?? 0)}%` }}
            />
          </div>
          {name && (
            <div className={styles.progressFile}>{name}</div>
          )}
        </div>
      )}
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
  const [progress, setProgress]     = useState(null);
  // git-specific repo selection
  const [availableRepos, setAvailableRepos] = useState([]);
  const [selectedRepos, setSelectedRepos]   = useState(new Set());
  // file-type selection (images / pptx / txt)
  const [availableFiles, setAvailableFiles] = useState([]);
  const [selectedFiles, setSelectedFiles]   = useState(new Set());

  function handleReposFound(repos) {
    setAvailableRepos(repos);
    setSelectedRepos(new Set(repos)); // default: all selected
  }

  function handleFilesFound(files) {
    setAvailableFiles(files);
    setSelectedFiles(new Set(files)); // default: all selected
  }

  async function runOrganize() {
    if (!source.trim() || !dest.trim()) {
      setResult({ type: "error", label: "Error", text: "Source and destination directories are required." });
      setCliCommand(null);
      return;
    }

    if (tab.sourceCheck && availableRepos.length > 0 && selectedRepos.size === 0) {
      setResult({ type: "error", label: "Error", text: "No repositories selected. Please select at least one repository to move." });
      setCliCommand(null);
      return;
    }

    if (tab.fileCheck && availableFiles.length > 0 && selectedFiles.size === 0) {
      setResult({ type: "error", label: "Error", text: `No ${tab.fileLabel}s selected. Please select at least one file to move.` });
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
    if (tab.sourceCheck && selectedRepos.size > 0) {
      body.repo_paths = Array.from(selectedRepos);
    }
    if (tab.fileCheck && selectedFiles.size > 0) {
      body.file_paths = Array.from(selectedFiles);
    }

    setCliCommand(buildCurlCommand(tab.endpoint, body));
    setLoading(true);
    setResult(null);
    setProgress({ scanning: true });

    try {
      const res = await fetch(`${API_BASE}${tab.streamEndpoint}`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(body),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setResult({ type: "error", label: "Server Error", text: data.detail ?? JSON.stringify(data, null, 2) });
        setProgress(null);
        return;
      }

      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let   buffer  = "";
      let   completeSummary = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep incomplete last line

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          let event;
          try { event = JSON.parse(line.slice(6)); } catch { continue; }

          if (event.type === "scanning") {
            setProgress({ scanning: true });
          } else if (event.type === "scan_complete") {
            setProgress({ scanning: false, current: 0, total: event.total, percent: 0, name: "" });
          } else if (event.type === "progress") {
            setProgress({ scanning: false, current: event.current, total: event.total, percent: event.percent, name: event.name });
          } else if (event.type === "complete") {
            completeSummary = event.summary;
            setProgress({ scanning: false, current: event.moved + (event.errors ?? 0), total: event.moved + (event.errors ?? 0), percent: 100, name: "" });
          }
        }
      }

      if (completeSummary !== null) {
        const summary = [
          `Source:        ${source.trim()}`,
          `Destination:   ${dest.trim()}`,
          `Copy retained: ${retainCopy ? "Yes" : "No"}`,
          "",
          completeSummary,
        ].join("\n");
        setResult({ type: "success", label: "Complete", text: summary });
      }

    } catch {
      setResult({
        type:  "error",
        label: "Connection Error",
        text:  `Could not reach the API at ${API_BASE}.\n\nMake sure the server is running:\n  bash script/bash/run_uv.sh`,
      });
      setProgress(null);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !loading) runOrganize();
  }

  const sourceBadge = tab.sourceCheck
    ? <GitRepoBadge path={source} onReposFound={handleReposFound} />
    : tab.fileCheck
      ? <FileBadge path={source} checkEndpoint={tab.checkEndpoint} fileLabel={tab.fileLabel} onFilesFound={handleFilesFound} />
      : null;

  return (
    <div onKeyDown={handleKeyDown}>
      <p className={styles.subtitle}>{tab.subtitle}</p>
      {tab.hint && <p className={styles.hint}>{tab.hint}</p>}

      <Field label="Source Directory"      id={`${tab.key}-source`} value={source} onChange={setSource} placeholder="/path/to/source" badge={sourceBadge} />

      {tab.sourceCheck && (
        <RepoSelector
          repos={availableRepos}
          selected={selectedRepos}
          onChange={setSelectedRepos}
          label="Select all repos"
        />
      )}

      {tab.fileCheck && (
        <RepoSelector
          repos={availableFiles}
          selected={selectedFiles}
          onChange={setSelectedFiles}
          label="Select all"
        />
      )}

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

      <Progress state={progress} />
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
