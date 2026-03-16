export default function PipelineStatus({ pipeline }) {
    if (!pipeline) return null;

    return (
        <div className="card">
            <strong>{pipeline.stage}</strong> — {pipeline.message}
        </div>
    );
}
