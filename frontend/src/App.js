import React, { useState } from "react";
import FileUpload from "./components/FileUpload";
import DataTable from "./components/DataTable";
import ChatInterface from "./components/ChatInterface";
import Visualization from "./components/Visualization";

const TABS = ["Overview", "Ask Questions", "Insights"];

const INITIAL_MESSAGES = [
  {
    role: "assistant",
    content:
      "Hi! Upload a CSV and ask me anything about your data — trends, summaries, filters, and more.",
  },
];

export default function App() {
  const [datasetInfo, setDatasetInfo] = useState(null);
  const [activeTab, setActiveTab] = useState("Overview");

  // Keep chat history here so it survives tab changes
  const [messages, setMessages] = useState(INITIAL_MESSAGES);

  const handleUploadSuccess = (data) => {
    setDatasetInfo(data);

    // Start a fresh chat for the newly uploaded dataset
    setMessages(INITIAL_MESSAGES);

    // Automatically go to Overview after upload
    setActiveTab("Overview");
  };

  return (
    <div className="app-container">

      {/* Header */}
      <div className="app-header">
        <div className="eyebrow">System Online</div>

        <h1>Intelligent CSV Analytics Assistant</h1>

        <p>
          Ask questions about your data in plain English — powered by
          Ollama &amp; RAG
        </p>
      </div>

      {/* CSV Upload */}
      <FileUpload onUploadSuccess={handleUploadSuccess} />

      {datasetInfo && (
        <>
          {/* Tabs */}
          <div className="tabs">
            {TABS.map((tab) => (
              <div
                key={tab}
                className={`tab ${
                  activeTab === tab ? "active" : ""
                }`}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </div>
            ))}
          </div>

          {/* Tab Content */}
          <div className="tab-panel">

            {activeTab === "Overview" && (
              <DataTable datasetInfo={datasetInfo} />
            )}

            {activeTab === "Ask Questions" && (
              <ChatInterface
                messages={messages}
                setMessages={setMessages}
              />
            )}

            {activeTab === "Insights" && (
              <Visualization datasetInfo={datasetInfo} />
            )}

          </div>
        </>
      )}
    </div>
  );
}