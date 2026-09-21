# Architecture Specification & Implementation Plan: LexiBridge Hybrid-Cloud MCP

This system specification blueprint is structured explicitly for **Claude Code** (or similar terminal-based agentic frameworks) to automatically generate, verify, and orchestrate the codebase of a private, high-security bilingual (English/Hindi) legal orchestration system.

---

## 🏗️ Core System Architecture Diagram

```
========================================================================================
                                🔒 SECURE DEPLOYMENT BOUNDARY
========================================================================================

 [ 🖥️ OFFLINE ENGINE / USER HOST ]
 
   +-----------------------+        (1) Read Files
   |   5 TB Google Drive   | ----------------------------+
   | (Client Legal Vault)  |                             |
   +-----------------------+                             v
                                            +--------------------------+
   +-----------------------+                |                          |
   | Local Console Context |                |    embed_offline.py      |
   |    (Claude Code)      |                | (ONNX Multilingual MiniLM|
   +-----------------------+                |  Local Matrix Compiler)  |
               |                            +--------------------------+
               | (4) Invokes Tool                        |
               v                                         | (2) Generate 384-Dim
   +-----------------------+                             |     Vector Coordinates
   |  Local HTTP Client    |                             v
   | (JSON-RPC over HTTPS) |                +--------------------------+
   +-----------------------+                |   my_manual_vector.json  |
               |                            +--------------------------+
               |                                         |
               +=================== HTTPS =======================+
                                   (Internet)            |
                                                         | (3) Push Coordinates
                                                         v     ONLY (Text stays local)
========================================================================================
                      ☁️ PUBLIC CLOUD BOUNDARY (Railway / FastMCP Cloud)
========================================================================================

 [ 📡 CLOUD BACKEND ENGINE ]
 
         +--------------------------------------------------------+
         |           Railway Managed Server Instance              |
         |                 (server_cloud.py)                      |
         +--------------------------------------------------------+
                                     |
                                     | (5) Query Vector Coordinates
                                     v
                        +--------------------------+
                        |  Pinecone Serverless DB  |
                        |   (legal-vault-index)    |
                        +--------------------------+
```

---

## 🛠️ Components Strategy & Verification Matrix

### 1. Data Ingestion & Local Array Matrix Compiler (`embed_offline.py`)
*   **Purpose:** Streams legal data layers from your Google Drive account, segments sentences without severing logical legal contexts, and calculates 384-dimensional coordinates completely inside local device RAM using a runtime compilation engine.
*   **Infrastructure Requirements:** Bypasses heavy deep learning wrappers (like PyTorch). Runs completely using `optimum[onnxruntime]` on low-tier CPUs or older hardware drives.

### 2. Live Enterprise Bridge Endpoint (`server_cloud.py`)
*   **Purpose:** Exposes functional schemas (`query_vault_with_precomputed_vector`) via JSON-RPC structures back down to your terminal interface.
*   **Infrastructure Requirements:** Deployed continuously inside virtual runtime spaces hosted via **Railway**. It maintains zero persistent cache blocks to keep processing fast and light.

### 3. Remote Mathematical Memory Index (`Pinecone Serverless`)
*   **Purpose:** Maps document nodes completely on remote search fabrics.
*   **Infrastructure Requirements:** Configured as a 384-dimension vector matrix matching the exact output properties of our local tokenizers.

---

## 🚀 Execution Instructions for Claude Code

When you launch Claude Code inside this project workspace repository, prompt the agent with the following command sequence to automatically construct the architecture:

> *"Claude, initialize this project workspace by reading the architecture specification markdown file.
> 1. Generate `requirements.txt` containing `fastmcp>=0.1.0`, `pinecone-client>=3.0.0`, `numpy`, `tokenizers`, and `optimum[onnxruntime]`.
> 2. Generate a valid `Procfile` containing `web: python server_cloud.py`.
> 3. Construct the local compiler pipeline inside `embed_offline.py` utilizing the Xenova ONNX model framework.
> 4. Build the live API orchestration listener within `server_cloud.py` to route vector arrays securely into the remote Pinecone index.
> 5. Ensure all inputs are properly verified using standard python try-except safety assertions."*

---

## 🔒 Enterprise Compliance Guardrails
*   **Zero Text Exposure:** Raw contract wording or client case summaries are restricted entirely to your local device boundaries. The cloud infrastructure only receives clean, non-reversible float arrays.
*   **Low Footprint Execution:** By using ONNX model compilation layers instead of heavy PyTorch packages, initialization overhead scales efficiently under tight computational conditions.