export default function MitreTable({ mapping }) {
    return (
        <div className="card">
            <h3>MITRE ATT&CK Mapping</h3>
            <table>
                <thead>
                    <tr>
                        <th>Tactic</th>
                        <th>Technique</th>
                    </tr>
                </thead>
                <tbody>
                    {mapping.length === 0 && (
                        <tr><td colSpan="2">No techniques detected</td></tr>
                    )}
                    {mapping.map((m, i) => (
                        <tr key={i}>
                            <td>{m.tactic}</td>
                            <td>{m.technique}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
