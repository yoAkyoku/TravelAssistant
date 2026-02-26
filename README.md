# TravelAssistant
智能旅遊助手 — 結合 LLM Agent Workflow 與工具調用的個人化旅遊規劃系統。

## 📌 專案簡介

TravelAssistant 是基於 Agent 架構的旅遊規劃系統，透過多階段推理流程，將使用者自然語言需求轉換為結構化偏好資訊，並生成多版本行程草案，整合住宿資訊後輸出最佳化旅遊計畫。

[Demo](https://youtu.be/nY7TSJ2zA04)

## 🧠 系統架構概念

水平流程展示整個 Agent Workflow：

```text
User Input  →  Preference Extraction  →  Draft Generation  →  Tool Calling  →  Plan Refinement  →  Frontend Rendering
```

### 流程說明

1. **User Input** — 使用者建立行程請求，輸入目的地與需求。
2. **Preference Extraction** — Agent 將自然語言轉換為結構化偏好資料（目的地、時間安排和旅遊主題等）。
3. **Draft Generation** — 根據偏好生成多個主題行程草案（美食 / 文化 / 動漫等）。
4. **Tool Calling** — 查詢當地住宿及相關資訊。
5. **Plan Refinement** — 根據住宿位置優化行程動線。
6. **Frontend Rendering** — 將最終行程與住宿資訊回傳前端展示。

## 🧩 技術棧

### Backend

* FastAPI
* LangGraph
* OpenAI API
* PostgreSQL

### Frontend

* Flask
* HTML / CSS / JavaScript

### DevOps

* Docker
* Docker Compose

## 📁 專案結構

```text
TravelAssistant/
│── backend/             # FastAPI + Agent Workflow
│── frontend/            # Flask 前端服務
│── docker-compose.yml
│── .env
│── workflow.png         # 系統流程圖
│── Demo.mp4             # 操作示範
```

## ▶️ 快速開始

### 1️⃣ Clone 專案

```bash
git clone https://github.com/yoAkyoku/TravelAssistant.git
cd TravelAssistant
```

### 2️⃣ 設定環境變數

建立 `.env`

```text
OPENAI_API_KEY={YOUR_OPENAI_API_KEY}
X_RAPIDAPI_KEY={YOUR_RAPIDAPI_API_KEY}
```

### 3️⃣ 啟動服務

```bash
docker-compose up -d --build
```

## 🎯 設計亮點

* 多階段 Agent Workflow
* 結構化資料作為中間狀態
* 多草案生成策略
* Tool Calling 與模型推理分離
* 動線優化
* 可擴展主題式旅遊模組

## 📌 未來優化方向

* 使用真實第三方旅遊 API
* 地圖視覺化整合
* 多語系支援
* 使用者帳戶與歷史紀錄保存
* 快取機制優化生成速度
