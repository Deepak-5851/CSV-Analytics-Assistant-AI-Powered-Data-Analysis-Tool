import React, { useState, useRef, useEffect } from "react";
import { askQuestion } from "../api";

export default function ChatInterface({ messages, setMessages }) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const chatEndRef = useRef(null);

  // Automatically scroll to the latest message
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const question = input.trim();

    // Add user's question immediately
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: question,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const response = await askQuestion(question);

      // Add AI response
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.data.answer,
        },
      ]);
    } catch (err) {
      const detail =
        err.response?.data?.detail ||
        "Something went wrong. Please try again.";

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: detail,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="card">

      <h3>Ask Your Data</h3>

      {/* Chat messages */}
      <div className="chat-window">

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`chat-message ${msg.role}`}
          >
            {msg.content}
          </div>
        ))}

        {loading && (
          <div className="chat-message assistant">
            Thinking...
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <div className="chat-input-row">

        <input
          type="text"
          placeholder="e.g. What is the average value of column X?"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />

        <button
          className="btn"
          onClick={handleSend}
          disabled={loading || !input.trim()}
        >
          {loading ? "Thinking..." : "Send"}
        </button>

      </div>

    </div>
  );
}