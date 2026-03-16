import { Bar } from "react-chartjs-2";

export default function SeverityChart({ severity }) {
    const levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
    const values = levels.map(l => l === severity ? 1 : 0);

    const data = {
        labels: levels,
        datasets: [{
            label: "Severity",
            data: values,
            backgroundColor: ["green", "yellow", "orange", "red"]
        }]
    };

    return (
        <div className="card">
            <h3>Severity Level</h3>
            <Bar data={data} />
        </div>
    );
}
