export default function LeakageTable({ indicators }) {
  if (!indicators || indicators.length === 0) {
    return <p>No leakage indicators detected</p>;
  }

  return (
    <table border="1" width="100%">
      <thead>
        <tr>
          <th>Type</th>
          <th>Confidence</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>
        {indicators.map((i, idx) => (
          <tr key={idx}>
            <td>{i.type}</td>
            <td>{i.confidence}</td>
            <td>{i.details}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
