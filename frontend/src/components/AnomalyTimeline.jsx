import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend);

export default function AnomalyTimeline({ history }) {
  if (!history || history.length === 0) {
    return <p>No anomaly trend data available yet.</p>;
  }

  const labels = history.map((h) => {
    if (!h.timestamp) return "Unknown";
    const dt = new Date(h.timestamp);
    return Number.isNaN(dt.getTime()) ? h.timestamp : dt.toLocaleString();
  });

  const data = {
    labels,
    datasets: [
      {
        label: "Anomaly Score",
        data: history.map((h) => Number(h.anomaly_score || 0)),
        borderColor: "#38bdf8",
        backgroundColor: "rgba(56, 189, 248, 0.2)",
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        display: true,
      },
    },
    scales: {
      y: {
        min: 0,
        max: 100,
      },
    },
  };

  return <Line data={data} options={options} />;
}
