import React from "react";

export default function DataTable({ datasetInfo }) {
  if (!datasetInfo) return null;

  const { filename, rows, columns, column_names, dtypes, missing_values, preview } = datasetInfo;

  return (
    <div className="card">
      <h3>Dataset Overview</h3>
      <div className="meta-row">
        <span><strong>File</strong> {filename}</span>
        <span><strong>Rows</strong> <span className="accent">{rows}</span></span>
        <span><strong>Columns</strong> <span className="accent">{columns}</span></span>
      </div>

      <div className="stat-grid">
        {column_names.map((col) => (
          <div className="stat-card" key={col}>
            <h4>{col}</h4>
            <p style={{ margin: 0 }}>Type: {dtypes[col]}</p>
            <p style={{ margin: 0 }}>Missing: {missing_values[col]}</p>
          </div>
        ))}
      </div>

      <h4 style={{ marginTop: 20 }}>Preview (first 5 rows)</h4>
      <div style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              {column_names.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preview.map((row, idx) => (
              <tr key={idx}>
                {column_names.map((col) => (
                  <td key={col}>{String(row[col])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
