import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";
import api from "../api/client";
import AnomalyGauge from "../components/AnomalyGauge";
import AnomalyTimeline from "../components/AnomalyTimeline";

const ANOMALY_THRESHOLD = 45;

export default function Dashboard({ view = "analyze" }) {
  const [authorized, setAuthorized] = useState(null);
  const [selectedReportId, setSelectedReportId] = useState("");
  const [analyzeArmed, setAnalyzeArmed] = useState(false);
  const [currentReportModalOpen, setCurrentReportModalOpen] = useState(false);
  const [historyModal, setHistoryModal] = useState({
    open: false,
    loading: false,
    report: null,
  });
  const [data, setData] = useState({
    analysis: {},
    runtime: {},
    history: [],
    entries: [],
    reports: [],
    selected_report_id: "",
  });
  const navigate = useNavigate();
  const monitorRef = useRef({ active: false, timerId: null });
  const latestUploadResultKeyRef = useRef("");

  const checkAuth = async () => {
    try {
      await api.get("/auth/me");
      setAuthorized(true);
    } catch {
      setAuthorized(false);
      navigate("/");
    }
  };

  const fetchData = async (reportId = selectedReportId) => {
    try {
      const params = reportId ? { report_id: reportId } : {};
      const res = await api.get("/dashboard/data", { params });
      setData(res.data);
      if (Object.prototype.hasOwnProperty.call(res.data || {}, "selected_report_id")) {
        setSelectedReportId(res.data.selected_report_id || "");
      }
    } catch {
      // Preserve previous state on transient failure.
    }
  };

  const openHistoryReport = async (reportId) => {
    setHistoryModal({ open: true, loading: true, report: null });
    try {
      const res = await api.get("/dashboard/data", { params: { report_id: reportId } });
      setHistoryModal({
        open: true,
        loading: false,
        report: {
          analysis: res.data?.analysis || {},
          entries: res.data?.entries || [],
        },
      });
    } catch {
      setHistoryModal({
        open: true,
        loading: false,
        report: {
          analysis: { uploaded_file: "Unavailable", severity: "N/A", risk_score: "N/A" },
          entries: [],
        },
      });
    }
  };

  const stopProcessingMonitor = () => {
    monitorRef.current.active = false;
    if (monitorRef.current.timerId) {
      clearTimeout(monitorRef.current.timerId);
      monitorRef.current.timerId = null;
    }
  };

  const monitorUntilAnalysisDone = (reportId = "") => {
    stopProcessingMonitor();
    monitorRef.current.active = true;

    const poll = async () => {
      if (!monitorRef.current.active) return;
      try {
        const params = reportId ? { report_id: reportId } : {};
        const res = await api.get("/dashboard/data", { params });
        setData(res.data);
        if (Object.prototype.hasOwnProperty.call(res.data || {}, "selected_report_id")) {
          setSelectedReportId(res.data.selected_report_id || "");
        }

        const processing = res.data?.analysis?.status === "PROCESSING";
        if (!processing) {
          stopProcessingMonitor();
          return;
        }
      } catch {
        // Retry while monitoring until success or component unmount.
      }
      monitorRef.current.timerId = setTimeout(poll, 2500);
    };

    poll();
  };

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (!authorized) return;
    fetchData("");
  }, [authorized]);

  useEffect(() => {
    return () => stopProcessingMonitor();
  }, []);

  useEffect(() => {
    if (!analyzeArmed) return;
    if (data.analysis?.status === "PROCESSING") return;

    const reportKey = data.analysis?.report_id || data.analysis?.timestamp || "";
    if (!reportKey) return;
    if (latestUploadResultKeyRef.current === reportKey) return;

    latestUploadResultKeyRef.current = reportKey;
    setCurrentReportModalOpen(true);
  }, [analyzeArmed, data.analysis]);

  const trendHistory = useMemo(() => {
    if (Array.isArray(data.reports) && data.reports.length > 0) {
      return data.reports
        .slice()
        .reverse()
        .map((report) => ({
          timestamp: report.timestamp,
          anomaly_score: Number(report.risk_score ?? report.anomaly_score ?? 0),
        }));
    }
    return data.analysis?.timestamp
      ? [{ timestamp: data.analysis.timestamp, anomaly_score: Number(data.analysis?.risk_score ?? 0) }]
      : [];
  }, [data.reports, data.analysis]);

  const anomalies = useMemo(
    () => buildAnomalyRows(data.analysis || {}, data.history || []),
    [data.analysis, data.history]
  );
  const flaggedEntries = useMemo(
    () => (Array.isArray(data.analysis?.flagged_entries) ? data.analysis.flagged_entries : []),
    [data.analysis]
  );
  const historyReports = useMemo(() => {
    if (!Array.isArray(data.reports)) return [];
    const currentId = data.analysis?.report_id || data.selected_report_id || "";
    return data.reports.filter((r) => r.report_id !== currentId);
  }, [data.reports, data.selected_report_id, data.analysis]);
  const showAnalyzeResult = useMemo(() => {
    if (!analyzeArmed) return false;
    if (data.analysis?.status === "PROCESSING") return false;
    return Boolean(data.analysis?.report_id || data.analysis?.timestamp);
  }, [analyzeArmed, data.analysis]);

  if (authorized === null) {
    return <p style={styles.loading}>Checking session...</p>;
  }

  return (
    <div style={styles.page}>
      <div style={styles.main}>
        <div style={styles.hero}>
          <h1 style={styles.title}>SOC Workbench</h1>
          <p style={styles.subtitle}>Upload a file to analyze. History cards open previous reports in a popup.</p>
        </div>

        <div style={styles.toolbar}>
          <UploadSection
            onUpload={() => {
              setAnalyzeArmed(true);
              setCurrentReportModalOpen(false);
              latestUploadResultKeyRef.current = "";
              setSelectedReportId("");
              monitorUntilAnalysisDone("");
            }}
            compact
          />
          {view !== "analyze" ? (
            <div style={styles.selectorCard}>
              <label style={styles.selectorLabel}>Active Report</label>
              <select
                value={selectedReportId}
                onChange={(e) => {
                  const id = e.target.value;
                  setSelectedReportId(id);
                  fetchData(id);
                }}
                style={styles.selector}
              >
                <option value="">Latest / Processing</option>
                {(data.reports || []).map((report) => (
                  <option key={report.report_id} value={report.report_id}>
                    {(report.uploaded_file || "Uploaded Log") + " | " + (report.severity || "N/A")}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div style={styles.selectorCard}>
              <label style={styles.selectorLabel}>Analyze Mode</label>
              <div style={styles.currentReportText}>
                Upload a new file. Results appear here after analysis completes.
              </div>
            </div>
          )}
        </div>

        {data.analysis?.status === "PROCESSING" ? (
          <div style={styles.processingBanner}>
            Analyzing new file: {data.analysis?.uploaded_file || "uploaded log"}...
          </div>
        ) : null}

        {view === "analyze" ? (
          <>
            {showAnalyzeResult ? (
              <>
                <div style={styles.panelAppear}><Stats data={data} /></div>
                <div style={{ ...styles.graphGrid, ...styles.panelAppear }}>
                  <div style={styles.panel}>
                    <h3 style={styles.sectionTitle}>Current Risk Score</h3>
                    <AnomalyGauge score={Number(data.analysis?.risk_score ?? data.analysis?.anomaly_score ?? 0)} />
                  </div>
                  <div style={styles.panel}>
                    <h3 style={styles.sectionTitle}>Timeline vs Risk Score (Logs)</h3>
                    <AnomalyTimeline history={trendHistory} />
                  </div>
                </div>
                <div style={styles.panelAppear}><ReasonPanels analysis={data.analysis || {}} /></div>
                <div style={styles.panelAppear}><FlaggedEntriesTable entries={flaggedEntries} /></div>
                <div style={styles.panelAppear}><AllEntriesTable entries={data.entries || []} analysis={data.analysis || {}} /></div>
                <div style={styles.panelAppear}><AnomalyTable anomalies={anomalies} /></div>
              </>
            ) : (
              <div style={styles.panel}>
                <h3 style={styles.sectionTitle}>Analyze</h3>
                <p style={styles.muted}>No active analysis yet. Upload a file to generate report components.</p>
              </div>
            )}
            <HistorySection reports={historyReports} onOpenReport={openHistoryReport} />
          </>
        ) : null}

        {view === "reports" ? (
          <ReportList
            reports={data.reports || []}
            selectedReportId={selectedReportId}
            onSelect={(id) => {
              setSelectedReportId(id);
              fetchData(id);
            }}
          />
        ) : null}

      </div>

      <HistoryReportModal
        open={historyModal.open}
        loading={historyModal.loading}
        report={historyModal.report}
        reports={data.reports || []}
        title="Historical Report"
        onClose={() => setHistoryModal({ open: false, loading: false, report: null })}
      />
      <HistoryReportModal
        open={currentReportModalOpen}
        loading={false}
        report={{
          analysis: data.analysis || {},
          entries: data.entries || [],
        }}
        reports={data.reports || []}
        title="Latest Uploaded Report"
        onClose={() => setCurrentReportModalOpen(false)}
      />
    </div>
  );
}

function UploadSection({ onUpload, compact = false }) {
  const [status, setStatus] = useState("");

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      setStatus("Uploading and analyzing...");
      await api.post("/dashboard/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setStatus("Analysis started. New report will appear shortly.");
      onUpload();
    } catch {
      setStatus("Upload failed");
    } finally {
      e.target.value = "";
    }
  };

  return (
    <div style={{ ...styles.uploadCard, ...(compact ? styles.uploadCardCompact : {}) }}>
      <h3 style={styles.sidebarTitle}>Upload Log File</h3>
      <input type="file" onChange={handleUpload} style={styles.fileInput} />
      <p style={styles.uploadStatus}>{status}</p>
    </div>
  );
}

function ReportList({ reports, selectedReportId, onSelect }) {
  return (
    <div style={styles.panel}>
      <h3 style={styles.sectionTitle}>Report Navigator</h3>
      {reports.length === 0 ? (
        <p style={styles.muted}>No reports yet.</p>
      ) : (
        <div style={styles.reportGrid}>
          {reports.map((report) => {
            const active = report.report_id === selectedReportId;
            return (
              <button
                key={report.report_id}
                style={{
                  ...styles.reportItem,
                  ...(active ? styles.reportItemActive : {}),
                }}
                onClick={() => onSelect(report.report_id)}
              >
                <div style={styles.reportItemTop}>
                  <span style={styles.reportFile}>{report.uploaded_file || "Uploaded Log"}</span>
                  <span style={styles.reportSeverity}>{report.severity || "N/A"}</span>
                </div>
                <div style={styles.reportMeta}>
                  Risk: {report.risk_score ?? "N/A"} | {formatTimestamp(report.timestamp)}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function HistorySection({ reports, onOpenReport }) {
  return (
    <div style={styles.panel}>
      <h3 style={styles.sectionTitle}>History</h3>
      {reports.length === 0 ? (
        <p style={styles.muted}>No previous reports available.</p>
      ) : (
        <div style={styles.historyGrid}>
          {reports.map((report) => (
            <button
              key={report.report_id}
              style={styles.historyCard}
              onClick={() => onOpenReport(report.report_id)}
            >
              <div style={styles.historyCardTop}>
                <span style={styles.historyFile}>{report.uploaded_file || "Legacy Report"}</span>
                <span style={styles.historySeverity}>{report.severity || "N/A"}</span>
              </div>
              <span style={styles.historyMeta}>{formatTimestamp(report.timestamp)}</span>
              <span style={styles.historyRisk}>Risk Score: {report.risk_score ?? "N/A"}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function HistoryReportModal({ open, loading, report, reports, onClose, title = "Historical Report" }) {
  const modalContentRef = useRef(null);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [exportError, setExportError] = useState("");

  if (!open) return null;
  const analysis = report?.analysis || {};
  const entries = Array.isArray(report?.entries) ? report.entries : [];
  const flaggedEntries = Array.isArray(analysis?.flagged_entries) ? analysis.flagged_entries : [];
  const anomalies = buildAnomalyRows(analysis || {}, []);
  const timeline = Array.isArray(reports)
    ? reports
        .slice()
        .reverse()
        .map((item) => ({
          timestamp: item.timestamp,
          anomaly_score: Number(item.risk_score ?? item.anomaly_score ?? 0),
        }))
    : [];

  const handleExportPdf = async () => {
    if (!modalContentRef.current || exportingPdf) return;

    setExportingPdf(true);
    setExportError("");
    const element = modalContentRef.current;
    const originalStyle = {
      maxHeight: element.style.maxHeight,
      overflow: element.style.overflow,
    };
    const expandableSections = Array.from(
      element.querySelectorAll('[data-pdf-expandable="true"]')
    );
    const originalSectionStyles = expandableSections.map((section) => ({
      section,
      maxHeight: section.style.maxHeight,
      overflow: section.style.overflow,
      overflowX: section.style.overflowX,
      overflowY: section.style.overflowY,
    }));

    try {
      // Expand modal for capture so the PDF includes full scrollable content.
      element.style.maxHeight = "none";
      element.style.overflow = "visible";
      expandableSections.forEach((section) => {
        section.style.maxHeight = "none";
        section.style.overflow = "visible";
        section.style.overflowX = "visible";
        section.style.overflowY = "visible";
      });

      // Let layout settle after style changes before capturing.
      await new Promise((resolve) => setTimeout(resolve, 80));

      const fullWidth = Math.max(element.scrollWidth, element.clientWidth, 1);
      const fullHeight = Math.max(element.scrollHeight, element.clientHeight, 1);
      const maxCanvasPixels = 28000000; // Keep below browser canvas limits.
      const computedScale = Math.sqrt(maxCanvasPixels / (fullWidth * fullHeight));
      const safeScale = Math.max(0.6, Math.min(2, Number.isFinite(computedScale) ? computedScale : 1));

      const canvas = await html2canvas(element, {
        scale: safeScale,
        useCORS: true,
        backgroundColor: "#ffffff",
        width: fullWidth,
        height: fullHeight,
      });

      if (!canvas.width || !canvas.height) {
        throw new Error("Captured content is empty.");
      }

      const pdf = new jsPDF("p", "mm", "a4");
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();

      // Slice one large canvas into page-sized canvases to avoid blank PDF pages.
      const pageHeightPx = Math.max(
        1,
        Math.floor((canvas.width * pageHeight) / pageWidth)
      );
      let renderedPages = 0;

      for (let offsetY = 0; offsetY < canvas.height; offsetY += pageHeightPx) {
        const sliceHeight = Math.min(pageHeightPx, canvas.height - offsetY);
        const pageCanvas = document.createElement("canvas");
        pageCanvas.width = canvas.width;
        pageCanvas.height = sliceHeight;

        const ctx = pageCanvas.getContext("2d");
        if (!ctx) {
          throw new Error("Unable to render PDF page canvas.");
        }

        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, pageCanvas.width, pageCanvas.height);
        ctx.drawImage(
          canvas,
          0,
          offsetY,
          canvas.width,
          sliceHeight,
          0,
          0,
          canvas.width,
          sliceHeight
        );

        const renderHeightMm = (sliceHeight * pageWidth) / canvas.width;
        const pageImageData = pageCanvas.toDataURL("image/jpeg", 0.95);
        if (renderedPages > 0) {
          pdf.addPage();
        }
        pdf.addImage(pageImageData, "JPEG", 0, 0, pageWidth, renderHeightMm);
        renderedPages += 1;
      }

      if (renderedPages === 0) {
        throw new Error("No PDF pages were generated.");
      }

      const safeFileName = String(analysis?.uploaded_file || "report")
        .replace(/[^a-z0-9-_]+/gi, "_")
        .replace(/^_+|_+$/g, "")
        .toLowerCase();
      const fallbackId = String(analysis?.report_id || Date.now());
      pdf.save(`${safeFileName || "report"}_${fallbackId}.pdf`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown export error";
      setExportError(`PDF export failed: ${message}`);
    } finally {
      element.style.maxHeight = originalStyle.maxHeight;
      element.style.overflow = originalStyle.overflow;
      originalSectionStyles.forEach(({ section, maxHeight, overflow, overflowX, overflowY }) => {
        section.style.maxHeight = maxHeight;
        section.style.overflow = overflow;
        section.style.overflowX = overflowX;
        section.style.overflowY = overflowY;
      });
      setExportingPdf(false);
    }
  };

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div ref={modalContentRef} style={styles.modalCard} onClick={(e) => e.stopPropagation()}>
        <div style={styles.modalHeader}>
          <h3 style={{ margin: 0 }}>{title}</h3>
          <div style={styles.modalActions}>
            <button
              style={styles.modalExport}
              onClick={handleExportPdf}
              disabled={exportingPdf || loading}
            >
              {exportingPdf ? "Exporting..." : "Export PDF"}
            </button>
            <button style={styles.modalClose} onClick={onClose}>
              Close
            </button>
          </div>
        </div>
        {exportError ? <p style={styles.exportError}>{exportError}</p> : null}

        {loading ? (
          <p style={styles.muted}>Loading report...</p>
        ) : (
          <>
            <div style={styles.graphGrid}>
              <div style={styles.panel}>
                <h3 style={styles.sectionTitle}>Current Risk Score</h3>
                <AnomalyGauge score={Number(analysis?.risk_score ?? analysis?.anomaly_score ?? 0)} />
              </div>
              <div style={styles.panel}>
                <h3 style={styles.sectionTitle}>Timeline vs Risk Score (Logs)</h3>
                <AnomalyTimeline history={timeline} />
              </div>
            </div>
            <Stats data={{ analysis, runtime: {} }} />
            <ReasonPanels analysis={analysis} />
            <FlaggedEntriesTable entries={flaggedEntries} />
            <AllEntriesTable entries={entries} analysis={analysis} />
            <AnomalyTable anomalies={anomalies} />
          </>
        )}
      </div>
    </div>
  );
}

function Stats({ data }) {
  const { analysis = {}, runtime = {} } = data;
  const explanation = analysis.explanation || {};

  return (
    <div style={styles.stats}>
      <Stat title="Selected Report" value={analysis.uploaded_file || "N/A"} />
      <Stat title="Severity" value={analysis.severity || "N/A"} />
      <Stat title="Risk Score" value={analysis.risk_score ?? analysis.anomaly_score ?? "N/A"} />
      <Stat title="Anomaly Score" value={analysis.anomaly_score ?? "N/A"} />
      <Stat title="Flagged Entries" value={Array.isArray(analysis.flagged_entries) ? analysis.flagged_entries.length : 0} />
      <Stat title="Leakage Indicators" value={analysis.leakage_count ?? runtime.leakage_indicators ?? 0} />
      <Stat title="Recommendation" value={analysis.recommendation || "N/A"} />
      <Stat title="Risk Summary" value={explanation.summary || "N/A"} />
    </div>
  );
}

function ReasonPanels({ analysis }) {
  const anomalyBreakdown = Array.isArray(analysis.anomaly_breakdown) ? analysis.anomaly_breakdown : [];
  const riskBreakdown = analysis.risk_breakdown && typeof analysis.risk_breakdown === "object"
    ? analysis.risk_breakdown
    : {};
  const riskReasons = Array.isArray(analysis.explanation?.reasons) ? analysis.explanation.reasons : [];

  return (
    <div style={styles.reasonGrid}>
      <div style={styles.panel}>
        <h3 style={styles.sectionTitle}>Why This Risk Score</h3>
        {Object.keys(riskBreakdown).length === 0 ? (
          <p style={styles.muted}>No risk component breakdown available yet.</p>
        ) : (
          <ul style={styles.reasonList}>
            {Object.entries(riskBreakdown).map(([key, value]) => (
              <li key={key}>
                {key.replaceAll("_", " ")}: {value}
              </li>
            ))}
          </ul>
        )}
        {riskReasons.length > 0 ? (
          <>
            <h4 style={styles.reasonSubTitle}>Detected Reasons</h4>
            <ul style={styles.reasonList}>
              {riskReasons.map((reason, idx) => (
                <li key={`${reason}-${idx}`}>{reason}</li>
              ))}
            </ul>
          </>
        ) : null}
      </div>
      <div style={styles.panel}>
        <h3 style={styles.sectionTitle}>Why This Anomaly Score</h3>
        {anomalyBreakdown.length === 0 ? (
          <p style={styles.muted}>No anomaly feature breakdown available yet.</p>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Signal</th>
                <th style={styles.th}>Raw Signal</th>
                <th style={styles.th}>Weight</th>
                <th style={styles.th}>Contribution</th>
              </tr>
            </thead>
            <tbody>
              {anomalyBreakdown.map((item, idx) => (
                <tr key={`${item.name}-${idx}`}>
                  <td style={styles.td}>{item.name}</td>
                  <td style={styles.td}>{item.signal}</td>
                  <td style={styles.td}>{item.weight}</td>
                  <td style={styles.td}>{item.contribution}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function Stat({ title, value }) {
  return (
    <div style={styles.statCard}>
      <h4 style={styles.statTitle}>{title}</h4>
      <p style={styles.statValue}>{String(value)}</p>
    </div>
  );
}

function FlaggedEntriesTable({ entries }) {
  return (
    <div style={styles.panel}>
      <h3 style={styles.sectionTitle}>Flagged Entries (Selected Report)</h3>
      {entries.length === 0 ? (
        <p style={styles.muted}>No entries flagged by the model for this report.</p>
      ) : (
        <TableWrap>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Line</th>
                <th style={styles.th}>Timestamp</th>
                <th style={styles.th}>Source</th>
                <th style={styles.th}>Destination</th>
                <th style={styles.th}>Reason</th>
                <th style={styles.th}>Risk Contribution</th>
                <th style={styles.th}>Contribution %</th>
                <th style={styles.th}>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry, idx) => (
                <tr key={`${entry.line_number}-${idx}`}>
                  <td style={styles.td}>{entry.line_number ?? "N/A"}</td>
                  <td style={styles.td}>{entry.timestamp || "N/A"}</td>
                  <td style={styles.td}>{entry.src_ip || "N/A"}</td>
                  <td style={styles.td}>{entry.dst_ip || "N/A"}</td>
                  <td style={styles.td}>{entry.reason || "N/A"}</td>
                  <td style={styles.td}>{entry.risk_contribution ?? 0}</td>
                  <td style={styles.td}>{entry.risk_contribution_pct ?? 0}%</td>
                  <td style={styles.td}>{entry.confidence || "N/A"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableWrap>
      )}
    </div>
  );
}

function AllEntriesTable({ entries, analysis }) {
  return (
    <div style={styles.panel}>
      <h3 style={styles.sectionTitle}>All Entries (Selected Report)</h3>
      {entries.length === 0 ? (
        <p style={styles.muted}>
          {analysis?.report_source === "history"
            ? "Legacy report selected: row-level entries were not stored for this older run."
            : "No parsed rows available for this report."}
        </p>
      ) : (
        <div style={styles.tableWrapTall} data-pdf-expandable="true">
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Line</th>
                <th style={styles.th}>Timestamp</th>
                <th style={styles.th}>Type</th>
                <th style={styles.th}>Level</th>
                <th style={styles.th}>Action</th>
                <th style={styles.th}>Direction</th>
                <th style={styles.th}>Source</th>
                <th style={styles.th}>Destination</th>
                <th style={styles.th}>Bytes</th>
                <th style={styles.th}>Risk Flag</th>
                <th style={styles.th}>Leakage Flag</th>
                <th style={styles.th}>Leakage Types</th>
                <th style={styles.th}>Risk Contribution</th>
                <th style={styles.th}>Reason</th>
                <th style={styles.th}>Message</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry, idx) => (
                <tr key={`${entry.line_number}-${idx}`}>
                  <td style={styles.td}>{entry.line_number ?? "N/A"}</td>
                  <td style={styles.td}>{entry.timestamp || "N/A"}</td>
                  <td style={styles.td}>{entry.log_type || "N/A"}</td>
                  <td style={styles.td}>{entry.level || "N/A"}</td>
                  <td style={styles.td}>{entry.action || "N/A"}</td>
                  <td style={styles.td}>{entry.direction || "N/A"}</td>
                  <td style={styles.td}>{entry.src_ip || "N/A"}</td>
                  <td style={styles.td}>{entry.dst_ip || "N/A"}</td>
                  <td style={styles.td}>{entry.bytes_sent ?? "N/A"}</td>
                  <td style={styles.td}>{entry.risk_flagged ? "Yes" : "No"}</td>
                  <td style={styles.td}>{entry.leakage_flagged ? "Yes" : "No"}</td>
                  <td style={styles.td}>{entry.leakage_types || "-"}</td>
                  <td style={styles.td}>{entry.risk_contribution ?? 0}</td>
                  <td style={styles.td}>{entry.risk_reason || "-"}</td>
                  <td style={styles.td}>{entry.message || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function AnomalyTable({ anomalies }) {
  return (
    <div style={styles.panel}>
      <h3 style={styles.sectionTitle}>Anomaly Signals</h3>
      {anomalies.length === 0 ? (
        <p style={styles.muted}>No anomaly signals available.</p>
      ) : (
        <TableWrap>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Timestamp</th>
                <th style={styles.th}>Severity</th>
                <th style={styles.th}>Score</th>
                <th style={styles.th}>Type</th>
                <th style={styles.th}>Confidence</th>
                <th style={styles.th}>Details</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.map((row, idx) => (
                <tr key={`${row.timestamp}-${row.type}-${idx}`}>
                  <td style={styles.td}>{row.timestamp}</td>
                  <td style={styles.td}>{row.severity}</td>
                  <td style={styles.td}>{row.score}</td>
                  <td style={styles.td}>{row.type}</td>
                  <td style={styles.td}>{row.confidence}</td>
                  <td style={styles.td}>{row.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableWrap>
      )}
    </div>
  );
}

function TableWrap({ children }) {
  return (
    <div style={styles.tableWrap} data-pdf-expandable="true">
      {children}
    </div>
  );
}

function formatTimestamp(value) {
  if (!value) return "Unknown time";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function buildAnomalyRows(currentAnalysis, history) {
  const rows = [];
  const score = Number(currentAnalysis?.risk_score ?? currentAnalysis?.anomaly_score ?? 0);
  const severity = currentAnalysis?.severity || "UNKNOWN";
  const timestamp = currentAnalysis?.timestamp || "Unknown";
  const indicators = Array.isArray(currentAnalysis?.leakage_indicators)
    ? currentAnalysis.leakage_indicators
    : [];
  const flaggedEntries = Array.isArray(currentAnalysis?.flagged_entries)
    ? currentAnalysis.flagged_entries
    : [];

  flaggedEntries.forEach((entry) => {
    rows.push({
      timestamp: entry?.timestamp || timestamp,
      severity,
      score,
      type: "Model flagged entry",
      confidence: entry?.confidence || "N/A",
      details: `line ${entry?.line_number ?? "?"}: ${entry?.reason || "flagged"} (risk ${entry?.risk_contribution ?? 0})`,
    });
  });

  indicators.forEach((item) => {
    rows.push({
      timestamp,
      severity,
      score,
      type: item?.type || "Indicator",
      confidence: item?.confidence ?? "N/A",
      details: item?.details || item?.description || JSON.stringify(item),
    });
  });

  if (rows.length === 0 && score >= ANOMALY_THRESHOLD) {
    rows.push({
      timestamp,
      severity,
      score,
      type: "Score threshold",
      confidence: "High",
      details: `Risk score ${score} crossed threshold ${ANOMALY_THRESHOLD}`,
    });
  }

  if (rows.length === 0 && Array.isArray(history) && history.length > 0) {
    const last = history[history.length - 1];
    rows.push({
      timestamp: last?.timestamp || "Unknown",
      severity: last?.severity || "UNKNOWN",
      score: Number(last?.risk_score ?? last?.anomaly_score ?? 0),
      type: "Historical report",
      confidence: "N/A",
      details: "No direct signals in selected report; showing latest historical context.",
    });
  }

  return rows.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

const styles = {
  page: {
    minHeight: "100vh",
    background:
      "radial-gradient(circle at 10% 10%, rgba(37,99,235,0.12), transparent 36%), radial-gradient(circle at 90% 20%, rgba(16,185,129,0.12), transparent 30%), #f3f6fb",
    padding: "14px 20px 24px",
    fontFamily: "'IBM Plex Sans', 'Segoe UI', Tahoma, sans-serif",
    color: "#0f172a",
  },
  hero: {
    marginBottom: 18,
  },
  title: {
    margin: 0,
    fontSize: 32,
    letterSpacing: 0.2,
  },
  subtitle: {
    marginTop: 8,
    marginBottom: 0,
    color: "#475569",
  },
  layout: {
    display: "grid",
    gridTemplateColumns: "320px 1fr",
    gap: 16,
    alignItems: "start",
  },
  sidebar: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
    position: "sticky",
    top: 12,
  },
  main: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
    maxWidth: 1400,
    margin: "0 auto",
  },
  toolbar: {
    display: "grid",
    gridTemplateColumns: "minmax(280px, 360px) 1fr",
    gap: 12,
    alignItems: "stretch",
  },
  selectorCard: {
    background: "#ffffff",
    border: "1px solid #dbe3ef",
    borderRadius: 14,
    padding: 14,
    boxShadow: "0 8px 24px rgba(15,23,42,0.06)",
  },
  selectorLabel: {
    display: "block",
    fontSize: 13,
    color: "#64748b",
    marginBottom: 6,
    fontWeight: 600,
  },
  selector: {
    width: "100%",
    border: "1px solid #cbd5e1",
    borderRadius: 10,
    padding: "8px 10px",
    background: "#fff",
    color: "#0f172a",
  },
  currentReportText: {
    fontWeight: 600,
    color: "#0f172a",
  },
  loading: {
    padding: 30,
    fontSize: 16,
  },
  sidebarTitle: {
    marginTop: 0,
    marginBottom: 8,
    fontSize: 16,
  },
  uploadCard: {
    background: "#ffffff",
    border: "1px solid #dbe3ef",
    borderRadius: 14,
    padding: 14,
    boxShadow: "0 8px 24px rgba(15,23,42,0.06)",
  },
  uploadCardCompact: {
    marginBottom: 0,
  },
  fileInput: {
    width: "100%",
    marginBottom: 8,
  },
  uploadStatus: {
    margin: 0,
    color: "#475569",
    fontSize: 13,
  },
  reportListCard: {
    background: "#ffffff",
    border: "1px solid #dbe3ef",
    borderRadius: 14,
    padding: 14,
    boxShadow: "0 8px 24px rgba(15,23,42,0.06)",
    maxHeight: "70vh",
    overflow: "hidden",
  },
  reportListWrap: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    overflow: "auto",
    maxHeight: "62vh",
    paddingRight: 4,
  },
  reportItem: {
    textAlign: "left",
    border: "1px solid #dbe3ef",
    borderRadius: 10,
    background: "#f8fbff",
    padding: 10,
    cursor: "pointer",
  },
  reportItemActive: {
    border: "1px solid #1d4ed8",
    background: "#e8f0ff",
  },
  reportItemTop: {
    display: "flex",
    justifyContent: "space-between",
    gap: 8,
    marginBottom: 5,
  },
  reportFile: {
    fontWeight: 600,
    color: "#0f172a",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  reportSeverity: {
    fontSize: 12,
    fontWeight: 700,
    color: "#1d4ed8",
  },
  reportMeta: {
    fontSize: 12,
    color: "#475569",
  },
  historyGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
    gap: 10,
  },
  historyCard: {
    border: "1px solid #dbe3ef",
    borderRadius: 12,
    background: "#f8fbff",
    textAlign: "left",
    padding: "10px 12px",
    cursor: "pointer",
    display: "flex",
    flexDirection: "column",
    gap: 4,
  },
  historyCardTop: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 10,
  },
  historyFile: {
    fontWeight: 700,
    color: "#0f172a",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  historySeverity: {
    fontSize: 11,
    fontWeight: 700,
    color: "#1d4ed8",
  },
  historyRisk: {
    fontSize: 12,
    fontWeight: 700,
    color: "#334155",
  },
  historyMeta: {
    fontSize: 12,
    color: "#475569",
  },
  reportGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
    gap: 10,
  },
  stats: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: 10,
  },
  statCard: {
    background: "#ffffff",
    border: "1px solid #dbe3ef",
    borderRadius: 12,
    padding: "12px 14px",
    boxShadow: "0 6px 16px rgba(15,23,42,0.05)",
  },
  statTitle: {
    margin: 0,
    fontSize: 12,
    color: "#64748b",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  statValue: {
    margin: "7px 0 0",
    fontSize: 14,
    color: "#0f172a",
    fontWeight: 600,
    lineHeight: 1.3,
  },
  graphGrid: {
    display: "grid",
    gridTemplateColumns: "minmax(280px, 360px) 1fr",
    gap: 12,
  },
  reasonGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 12,
  },
  reasonSubTitle: {
    margin: "10px 0 6px",
    fontSize: 14,
  },
  reasonList: {
    margin: 0,
    paddingLeft: 18,
  },
  processingBanner: {
    background: "#fff7ed",
    border: "1px solid #fdba74",
    borderRadius: 10,
    padding: "10px 12px",
    color: "#9a3412",
    fontWeight: 600,
  },
  panelAppear: {
    animation: "fadeInUp 0.32s ease",
  },
  panel: {
    background: "#ffffff",
    border: "1px solid #dbe3ef",
    borderRadius: 14,
    padding: 14,
    boxShadow: "0 8px 24px rgba(15,23,42,0.06)",
  },
  sectionTitle: {
    marginTop: 0,
    marginBottom: 10,
  },
  muted: {
    color: "#64748b",
    margin: 0,
  },
  tableWrap: {
    overflowX: "auto",
  },
  tableWrapTall: {
    overflow: "auto",
    maxHeight: 480,
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: 13,
  },
  th: {
    textAlign: "left",
    borderBottom: "1px solid #dbe3ef",
    padding: "8px 7px",
    backgroundColor: "#f8fbff",
    position: "sticky",
    top: 0,
    zIndex: 1,
  },
  td: {
    borderBottom: "1px solid #edf2f7",
    padding: "8px 7px",
    verticalAlign: "top",
    color: "#1e293b",
  },
  modalOverlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(2, 6, 23, 0.55)",
    display: "grid",
    placeItems: "center",
    zIndex: 300,
    padding: 18,
  },
  modalCard: {
    width: "min(1100px, 96vw)",
    maxHeight: "90vh",
    overflow: "auto",
    background: "#ffffff",
    borderRadius: 14,
    border: "1px solid #dbe3ef",
    boxShadow: "0 18px 50px rgba(15,23,42,0.35)",
    padding: 14,
  },
  modalHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  modalActions: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  modalExport: {
    border: "1px solid #93c5fd",
    background: "#dbeafe",
    color: "#1d4ed8",
    borderRadius: 10,
    padding: "6px 10px",
    fontWeight: 600,
  },
  exportError: {
    margin: "0 0 10px",
    color: "#b91c1c",
    fontWeight: 600,
    fontSize: 13,
  },
  modalClose: {
    border: "1px solid #cbd5e1",
    background: "#f8fafc",
    borderRadius: 10,
    padding: "6px 10px",
  },
  modalStats: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: 8,
    marginBottom: 10,
    fontWeight: 600,
    color: "#334155",
  },
};
