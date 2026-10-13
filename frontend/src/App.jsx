import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend,
  CartesianGrid, ResponsiveContainer, ReferenceDot,
} from "recharts";
import { getSummary, getDetections, getReadings } from "./api";
import "./App.css";

const fmt = (t) => (t ? t.slice(5, 16).replace("T", " ") : "");

function Chart({ title, data, lines, detections, dotKey }) {
  return (
    <div className="panel">
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="reading_time" tickFormatter={fmt} minTickGap={40} />
          <YAxis />
          <Tooltip labelFormatter={fmt} />
          <Legend />
          {lines.map(([key, color]) => (
            <Line key={key} dataKey={key} stroke={color} dot={false} strokeWidth={2} />
          ))}
          {detections.map((d) => (
            <ReferenceDot key={d.detection_id} x={d.reading_time} y={d[dotKey]}
              r={5} fill="#e53935" stroke="none" />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function App() {
  const [summary, setSummary] = useState([]);
  const [selected, setSelected] = useState(null);
  const [readings, setReadings] = useState([]);
  const [detections, setDetections] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getSummary()
      .then((s) => { setSummary(s); if (s.length) setSelected(s[0].link_id); })
      .catch(() => setError("Cannot reach API at localhost:8000"));
  }, []);

  useEffect(() => {
    if (!selected) return;
    Promise.all([getReadings(selected), getDetections(selected)])
      .then(([r, d]) => { setReadings([...r].reverse()); setDetections(d); })
      .catch(() => setError("Failed to load link data"));
  }, [selected]);

  const times = new Set(readings.map((r) => r.reading_time));
  const visibleDets = detections.filter((d) => times.has(d.reading_time));

  return (
    <div className="app">
      <h1>NetSentinelWAN AI</h1>
      {error && <div className="error">{error}</div>}

      <div className="cards">
        {summary.map((s) => (
          <div key={s.link_id}
            className={`card ${selected === s.link_id ? "active" : ""}`}
            onClick={() => setSelected(s.link_id)}>
            <div className="card-title">{s.link_id}</div>
            <div className={`badge ${s.latest_anomaly_score !== null ? "bad" : "ok"}`}>
              {s.latest_anomaly_score !== null ? "Anomalous" : "Normal"}
            </div>
            <div>Latency: {s.latest_latency_ms} ms</div>
            <div>Loss: {s.latest_packet_loss_pct}%</div>
            <div>Util: {s.latest_utilization_pct}%</div>
            <div className="muted">{s.anomaly_count} anomalies</div>
          </div>
        ))}
      </div>

      {selected && (
        <>
          <h2>{selected}</h2>
          <div className="charts">
            <Chart title="Latency & Jitter (ms)" data={readings} detections={visibleDets}
              dotKey="latency_ms" lines={[["latency_ms", "#1e88e5"], ["jitter_ms", "#8e24aa"]]} />
            <Chart title="Packet Loss & Utilization (%)" data={readings} detections={visibleDets}
              dotKey="packet_loss_pct" lines={[["packet_loss_pct", "#e53935"], ["utilization_pct", "#43a047"]]} />
          </div>

          <div className="panel">
            <h3>Detected anomalies</h3>
            <table>
              <thead>
                <tr><th>Time</th><th>Score</th><th>Latency</th><th>Loss</th><th>Explanation</th></tr>
              </thead>
              <tbody>
                {detections.map((d) => (
                  <tr key={d.detection_id}>
                    <td>{fmt(d.reading_time)}</td>
                    <td>{d.anomaly_score.toFixed(3)}</td>
                    <td>{d.latency_ms}</td>
                    <td>{d.packet_loss_pct}</td>
                    <td>{d.explanation}</td>
                  </tr>
                ))}
                {!detections.length && <tr><td colSpan="5">No anomalies</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}