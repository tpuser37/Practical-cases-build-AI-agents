import React, { useState } from "react";
import axios from "axios";

function App() {
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([]);

  const sendMessage = async () => {
    if (!message) return;
    // Ajouter le message de l'utilisateur
    setChat([...chat, { sender: "user", text: message }]);
    setMessage("");

    try {
      const res = await axios.post("http://localhost:5000/chat", { message });
      setChat((prev) => [...prev, { sender: "bot", text: res.data.response }]);
    } catch (err) {
      setChat((prev) => [...prev, { sender: "bot", text: "Error: " + err.message }]);
    }
  };

  return (
    <div style={{ maxWidth: "600px", margin: "auto", padding: "20px" }}>
      <h1>HR Assistant Chatbot</h1>
      <div style={{ border: "1px solid #ccc", padding: "10px", minHeight: "300px" }}>
        {chat.map((c, i) => (
          <div key={i} style={{ textAlign: c.sender === "user" ? "right" : "left" }}>
            <b>{c.sender}:</b> {c.text}
          </div>
        ))}
      </div>
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        style={{ width: "80%", padding: "10px", marginRight: "5px" }}
      />
      <button onClick={sendMessage} style={{ padding: "10px 20px" }}>Send</button>
    </div>
  );
}

export default App;
