# 🎥 Video – Activepieces Claude Use Case

https://github.com/user-attachments/assets/80b1d467-c43e-47ac-b9b1-d15cbcf3e662

## 🧩 Overview

This use case shows how **Activepieces** is used as an **MCP Tool Server** to expose tools (pieces such as **Exa**) and how an **Claude** can connect to it via **Model Context Protocol (MCP)**.

The goal is to externalize tools from the agent and access them through a standard MCP interface.

---

## ⚙️ Steps

## 1. Create an Activepieces Account
- Create an account on **Activepieces**
- Access the workspace dashboard

---

## 2. Enable MCP Server
- Go to **Settings**
- Enable **MCP Server**
- Retrieve:
  - **MCP Server URL**
  - **MCP access token**

Activepieces now acts as an **MCP-compliant tool server**.

---

## 3. Add Exa as a Piece
- Go to **Pieces / Connections**
- Add the **Exa** piece
- Provide your **Exa API Key**

Result:
- Exa actions are available as tools
- These tools are exposed via the MCP server

---

## 4. Claude Integration
- Go to **Claude → Settings → Connectors**
- Add **Activepieces** as a connector
- Specify:
  - **MCP Server URL**
  - **MCP access token**
- Save the connector

Claude can now invoke tools exposed by Activepieces through MCP.





