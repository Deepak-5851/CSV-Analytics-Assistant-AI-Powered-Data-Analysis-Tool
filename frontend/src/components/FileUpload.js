import React, { useRef, useState } from "react";
import { uploadCSV } from "../api";

export default function FileUpload({ onUploadSuccess }) {
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fileName, setFileName] = useState(null);

  const handleFile = async (file) => {
    if (!file) return;
    setFileName(file.name);
    setError(null);
    setLoading(true);
    try {
      const response = await uploadCSV(file);
      onUploadSuccess(response.data.dataset_info);
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  return (
    <div className="card">
      <div
        className="upload-box"
        onClick={() => fileInputRef.current.click()}
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        <p style={{ margin: 0, fontWeight: 600 }}>
          {fileName ? `Selected: ${fileName}` : "Click or drag a CSV file here to upload"}
        </p>
        <p style={{ margin: "6px 0 0 0", fontSize: 13, color: "#888" }}>
          Supports .csv files only
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          style={{ display: "none" }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>
      {loading && <p style={{ marginTop: 10 }}>Uploading and building index...</p>}
      {error && <p style={{ marginTop: 10, color: "crimson" }}>{error}</p>}
    </div>
  );
}
