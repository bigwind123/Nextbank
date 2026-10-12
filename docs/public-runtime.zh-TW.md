# 本機 runtime

此 checkout 提供兩種不同的瀏覽體驗：

- [本機執行介面](../app.html) 會呼叫 `public_app` Flask 服務。Workspace、模型、核准紀錄、Gateway 操作、OCR 案件與對話會保存於預設的 `.local/runtime` SQLite 資料庫。
- [離線介面示例](../demo.html?module=gateway) 是依來源介面重建的靜態頁面，使用固定合成狀態，不會呼叫 runtime 或 Python 範例，重新載入後狀態即重設。

## 啟動

需要 Python 3.11 以上版本；此 checkout 以 Python 3.14.5 驗證。於專案根目錄建立虛擬環境、安裝 runtime 依賴並啟動服務。

**Windows PowerShell**

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-runtime.txt
.venv\Scripts\python.exe -m public_app
```

**macOS / Linux**

```console
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-runtime.txt
.venv/bin/python -m public_app
```

安裝 `requirements-runtime.txt` 後，可執行完整 runtime 與 Python 範例測試套件：

**Windows PowerShell**

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**macOS / Linux**

```console
.venv/bin/python -m unittest discover -s tests -v
```

開啟 <http://127.0.0.1:8000/>。服務預設只綁定 loopback。本機操作介面沒有登入驗證，請只在本機使用，不要將連接埠暴露至網路。應用介面由此 runtime 提供；以 `file://` 開啟 `app.html` 不會啟動 API。

## 本機實際功能與資料邊界

- **Gateway：** Flask 服務管理本機 Workspace／模型目錄，並將 Workspace 核准與 provider 選用分開記錄。設定 LiteLLM 管理端點後，選用會寫入原生 Team，並透過讀回確認 Team 狀態。模型 Runtime 使用狀態仍須另外驗證。本機逾時情境只用於本機 registry。
- **OCR：** RapidOCR 預設於本機 CPU 辨識 PNG/JPEG 圖片。在本次全新 Windows 安裝驗證中，RapidOCR wheel 已包含預設 ONNX 模型，首次辨識直接載入本機模型，沒有另外下載模型。文件紀錄會加密保存於本機 SQLite vault。選用已設定的 VLM 時，未修改的原始圖片會傳送至操作者設定的視覺模型端點；VLM 收到圖片前不會先去識別化。上傳前介面要求明確確認。除非端點及資料處理方式適合該文件，請只使用合成文件。
- **評估：** 本機驗證只檢查欄位存在及型別，不會重新計算財務公式或資格。設定 LLM 評估時，只會傳送限縮後的欄位白名單 profile；姓名與帳號值會以文件範圍 token 取代，不會傳送原始圖片、OCR 原文、來源識別碼或來源行資訊，provenance 只保留欄位名稱。這是資料假名化，不是不可逆匿名化。除非端點及資料處理方式適合該案件，請只使用合成文件。
- **搜尋與聊天：** 未設定 Elasticsearch 時，搜尋使用包含合成操作事件的本機 SQLite FTS5 索引；聊天搜尋會回傳所選搜尋後端的實際結果。模型聊天會呼叫操作者設定的端點，需先設定模型資訊才可使用。
- **MCP route：** `/mcp` 接受受限制的 JSON-RPC `tools/list` 與 `tools/call` 子集，要求 `context.active_skill="elasticsearch-ops"`，僅提供公開版搜尋工具子集。它不是完整通用 MCP server，也不是可直接替代標準 MCP 用戶端的端點。

## 端點設定與資料保存

連線設定頁只保存端點網址和模型名稱，不提供或回傳 API key。請在已忽略追蹤的 `.local/runtime-config.json` 或伺服器環境變數設定憑證。支援的環境變數包含 `PORTFOLIO_MODEL_API_KEY`、`PORTFOLIO_LITELLM_API_KEY` 和 `PORTFOLIO_LITELLM_MASTER_KEY`。不要把憑證放入 URL 或提交本機設定檔。

API 會將請求傳送至操作者設定的模型、LiteLLM、VLM 或 Elasticsearch 端點，這些請求會離開本機程序。應用不包含這些服務、模型或憑證。Runtime 支援在本機忽略追蹤的設定檔或伺服器環境變數設定模型與 LiteLLM 憑證；Elasticsearch 整合只支援可直接連線且不需憑證的測試端點，不支援受保護叢集的認證。瀏覽器檢視狀態在重新載入後重設；runtime 資料則保存在本機 SQLite。獨立 Python 範例使用記憶體內的假 provider，不會寫入 runtime 資料庫。

需要不連網的視覺導覽時，請使用離線介面示例；要操作實際 Flask 路由與本機持久化資料時，請啟動本機 runtime。
