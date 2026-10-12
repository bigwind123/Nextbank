# AI Model Gateway 工程作品集

AI Model Gateway 是管理模型端點、Workspace 存取與共用用量的控制面。工程重點包括管理 Workspace 與模型權限、區分核准和原生 Team 設定，以及處理遠端寫入結果不明時的讀回核對。Gateway 管理 LiteLLM 原生物件；Financial OCR 與 Elasticsearch AIOps 是各自使用獨立推論端點的應用示例。本作品集呈現源自實際工程工作的設計與合成示例。

[開啟作品集](index.html) | [執行本機應用](app.html) | [Gateway 離線示例](demo.html?module=gateway) | [OCR 離線示例](demo.html?module=ocr) | [Elasticsearch 對話離線示例](demo.html?module=chat) | [English runtime](app.en.html) | [English README](README.md)

## 此 checkout 可執行的內容

| 部分 | 本 checkout 提供的內容 |
| --- | --- |
| 本機 live app | `public_app` 是可執行的 Flask 服務，使用 SQLite 持久保存資料，提供 Gateway Workspace／模型核准與選用、操作讀回、本機事件搜尋、對話及實際 OCR。這是公開重建版，不包含原私人應用服務。 |
| 離線瀏覽器示例 | `demo*.html` 是依來源介面重建的靜態頁面，使用確定性合成狀態；不會呼叫 Flask app、模型、檔案或 Elasticsearch，重新載入後狀態會重設。 |
| Python 示例 | 可在本機執行的範例邏輯，涵蓋冪等處理與不確定寫入讀回、AES-GCM token 對應與欄位設定，以及 MCP 工具可見性和派送檢查。Provider 與資料皆為記憶體內 fixture。 |
| 選用外部服務 | LiteLLM 管理、模型推論、VLM 與 Elasticsearch 僅在操作者自行設定端點後才會呼叫。此 runtime 不含模型或 Elasticsearch 服務。原私人專案的部署成果及完整追蹤的 CI/CD pipeline 不在此公開 checkout。 |

已正式寫入的 live runtime 使用本機 SQLite；端點連線與文件外送邊界請參閱[本機 runtime 說明](docs/public-runtime.zh-TW.md)。

Live app 記錄持久保存於 `.local/runtime` SQLite；其瀏覽器檢視狀態會在重新載入後重設。離線示例狀態也會在重新載入後重設；獨立 Python 示例的操作、provider 與假名紀錄則只存在於該程序記憶體。

![平台架構圖](assets/diagrams/platform-overview.svg)

## 啟動本機應用

需要 Python 3.11 以上版本；本 checkout 以 Python 3.14.5 實測。於作品集資料夾建立虛擬環境、安裝 runtime 相依套件並啟動只綁定 loopback 的服務。連線設定頁只接受端點網址和模型名稱；憑證請放在已忽略追蹤的 `.local/runtime-config.json` 或環境變數。

**Windows PowerShell：**

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-runtime.txt
.venv\Scripts\python.exe -m public_app
```

**macOS / Linux：**

```console
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-runtime.txt
.venv/bin/python -m public_app
```

開啟 <http://127.0.0.1:8000/> 使用 live runtime。操作台沒有驗證機制，請只在本機使用，不要曝露連接埠。RapidOCR 預設於本機 CPU 執行；VLM 則會將未遮罩的原始圖片傳送至操作者設定的端點，收到圖片前不會去識別化。LLM 評估僅傳送欄位白名單；姓名與帳號值會以文件範圍 token 取代，不包含原始圖片、OCR 原文、來源識別碼與原始行資料；這是假名化，不是不可逆的匿名化。Elasticsearch 需由使用者提供可直接連線、無需認證的測試端點。更多資料保存與端點邊界見[本機 runtime 說明](docs/public-runtime.zh-TW.md)。

更多執行與資料邊界請見[本機 runtime 說明](docs/public-runtime.zh-TW.md)。

### 本機示例預覽

[![Gateway 管理控制面預覽](assets/screenshots/platform-overview.png)](demo.html?module=gateway)

[Financial OCR 預覽](demo.html?module=ocr) · [Elasticsearch AIOps 預覽](demo.html?module=chat)

## 本機操作示例

在瀏覽器直接開啟 `index.html` 或上方模組連結，也可在作品集資料夾執行：

```console
python -m http.server 8000 --bind 127.0.0.1
```

這個區段只服務靜態作品集與離線操作示例，不會啟動上方提到的 live runtime。開啟 <http://127.0.0.1:8000/index.html> 可瀏覽靜態頁面；GitHub 只顯示 HTML 原始碼，不會代為託管應用程式。離線頁面使用合成 fixture，不會讀取本機文件或呼叫外部服務。

## 案例研究

| 案例 | 工程問題 | 案例內容 |
| --- | --- | --- |
| [AI Model Gateway](case-studies/model-gateway.md) | 如何治理模型存取與平台物件，同時維持管理面和推論流量分離？ | Flask 管理控制面、LiteLLM 原生物件、獨立推論路徑、核准與讀回狀態，以及系統邊界。 |
| [Financial OCR](case-studies/financial-ocr.md) | 如何降低文件處理的下游資料暴露並保留來源資訊？ | 圖片辨識第一階段、可還原個資假名、Profile 欄位白名單、精簡案例 payload 與回應 schema 檢查。 |
| [Elasticsearch AIOps](case-studies/operations-chatroom.md) | 對話流程如何提供搜尋工具並清楚呈現實際授權邊界？ | 技能範圍內的模型可見工具、JSON-RPC MCP、查詢限制、原系統 dispatch 限制及公開示例的加強措施。 |

Gateway 是平台案例；OCR 與 Elasticsearch 對話是周邊應用，其推論端點各自配置，不經 Gateway 管理服務轉送。

## 可重現公開示例

以下指令需要已安裝的 Python 3.14 interpreter；本機驗證使用 Python 3.14.5。請在作品集資料夾建立隔離環境，指令不需先啟用環境。

**Windows PowerShell：**

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python.exe examples/run_demo.py gateway
.venv\Scripts\python.exe examples/run_demo.py mcp
```

**macOS / Linux：**

```console
python3.14 -m venv .venv
.venv/bin/python examples/run_demo.py gateway
.venv/bin/python examples/run_demo.py mcp
```

Gateway 與 MCP 只使用 Python 標準函式庫。OCR、整合的 `all` 指令與測試需要 `cryptography` 進行 AES-GCM token 對應，執行前請先安裝：

```console
.venv/bin/python -m pip install -r requirements-demo.txt
.venv/bin/python examples/run_demo.py ocr
.venv/bin/python examples/run_demo.py all
.venv/bin/python -m unittest discover -s tests -p "test_examples.py" -v
```

Windows 請將上述 `.venv/bin/python` 換成 `.venv\Scripts\python.exe`。原聊天應用有已知的工具授權缺口；公開 Python sample 使用較嚴格預設，拒絕未知技能並依所選技能檢查工具 dispatch。這是公開示例新增的改善，不代表原系統原有此項控制。請參閱[公開示例說明](docs/public-sample.md)了解指令與範圍。

## 架構圖與授權聲明

[平台總覽圖](assets/diagrams/platform-overview.html)呈現 Gateway 管理與應用推論路徑的區別；其他圖包含 [Gateway 復原流程](assets/diagrams/gateway-recovery.html)、[OCR](assets/diagrams/financial-ocr.html)及 [Elasticsearch MCP](assets/diagrams/elasticsearch-mcp.html)。架構圖用於解說，不是部署畫面截圖。

架構圖使用 [Archify](https://github.com/tt-a1i/archify)，並保留其 MIT 授權全文於 [third_party/ARCHIFY_LICENSE](third_party/ARCHIFY_LICENSE)。其他資訊請見[第三方授權聲明](THIRD_PARTY_NOTICES.md)。

## 交付與負責範圍

我端到端負責 AI Model Gateway 與應用範圍，工作包含產品設計、應用程式實作、平台治理、部署與 CI/CD。原始私人專案包含部署相關成果；公開 checkout 現在另含可執行的本機 Flask/SQLite 重建版及獨立 Python 範例，但不含原私人後端服務、容器或 Helm 成果，也沒有完整追蹤的交付 pipeline。離線示例只使用合成狀態；本作品集不宣稱特定的即時部署或正式環境成效。

## 範圍

內部設定與真實營運或文件資料均已排除，或以通用合成示例取代；合成紀錄與指標會清楚標示。本作品集不複製私有原始碼庫。選材原則與已知限制請見 [CONTENT_SELECTION.md](CONTENT_SELECTION.md)。
