import React, { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

import { getStatistics, getSummary } from "../api";

export default function Visualization({ datasetInfo }) {
  const [stats, setStats] = useState(null);
  const [summary, setSummary] = useState("");
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [error, setError] = useState("");

  // Get statistics when Insights page opens
  useEffect(() => {
    if (!datasetInfo) return;

    const loadStatistics = async () => {
      try {
        setLoadingStats(true);
        setError("");

        const res = await getStatistics();

        setStats(res.data);
      } catch (err) {
        console.error("Statistics error:", err);

        const message =
          err.response?.data?.detail ||
          "Unable to load statistics. Please make sure the backend is running.";

        setError(message);
        setStats(null);
      } finally {
        setLoadingStats(false);
      }
    };

    loadStatistics();
  }, [datasetInfo]);

  // Generate AI summary
  const handleGenerateSummary = async () => {
    try {
      setLoadingSummary(true);
      setSummary("");

      const res = await getSummary();

      setSummary(
        res.data?.summary ||
          "No summary was generated."
      );
    } catch (err) {
      console.error("Summary error:", err);

      const message =
        err.response?.data?.detail ||
        "Could not generate summary. Please try again.";

      setSummary(message);
    } finally {
      setLoadingSummary(false);
    }
  };

  // Loading statistics
  if (loadingStats) {
    return (
      <div className="card">
        <h3>Statistical Insights</h3>
        <p>Loading statistics...</p>
      </div>
    );
  }

  // Statistics error
  if (error) {
    return (
      <div className="card">
        <h3>Statistical Insights</h3>

        <p>
          {error}
        </p>

        <button
          className="btn"
          onClick={() => window.location.reload()}
        >
          Retry
        </button>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="card">
        <h3>Statistical Insights</h3>
        <p>No statistics available.</p>
      </div>
    );
  }

  // Convert statistics to chart data
  const chartData = Object.entries(stats)
    .filter(
      ([, s]) =>
        s &&
        typeof s === "object" &&
        typeof s.mean === "number"
    )
    .map(([col, s]) => ({
      column: col,
      mean: s.mean,
      max: s.max,
      min: s.min,
    }));

  return (
    <div className="card">

      <h3>Statistical Insights</h3>

      {chartData.length > 0 ? (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>

            <CartesianGrid strokeDasharray="3 3" />

            <XAxis
              dataKey="column"
              style={{
                fontFamily: "JetBrains Mono",
                fontSize: 11,
              }}
            />

            <YAxis
              style={{
                fontFamily: "JetBrains Mono",
                fontSize: 11,
              }}
            />

            <Tooltip />

            <Legend />

            <Bar
              dataKey="mean"
              name="Average"
            />

            <Bar
              dataKey="max"
              name="Maximum"
            />

            <Bar
              dataKey="min"
              name="Minimum"
            />

          </BarChart>
        </ResponsiveContainer>
      ) : (
        <p>
          No numeric columns are available for visualization.
        </p>
      )}

      <button
        className="btn"
        style={{ marginTop: 16 }}
        onClick={handleGenerateSummary}
        disabled={loadingSummary}
      >
        {loadingSummary
          ? "Generating..."
          : "Generate AI Summary"}
      </button>

      {summary && (
        <p className="summary-block">
          {summary}
        </p>
      )}

    </div>
  );
}