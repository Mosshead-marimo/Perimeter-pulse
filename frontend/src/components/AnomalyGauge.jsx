import { Doughnut } from "react-chartjs-2";

export default function AnomalyGauge({ score }) {
    const safeScore = Math.max(0, Math.min(100, Number(score || 0)));

    const data = {
        labels: ["Risk", "Normal"],
        datasets: [{
            data: [safeScore, 100 - safeScore],
            backgroundColor: ["#ef4444", "#1f2937"]
        }]
    };

    return <Doughnut data={data} />;
}
