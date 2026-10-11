# 專案交付與驗證範圍

## 交付責任

我端到端負責 AI Model Gateway 與其應用範圍，工作涵蓋需求和產品設計、系統架構、程式實作、模型使用治理、部署與 CI/CD。Gateway 是平台管理控制面；Financial OCR 與 Elasticsearch AIOps 是其周邊應用，各自設定推論或工具端點。

這份公開作品集以重新整理的文件、圖示及合成示例呈現上述工作。原始專案的檔案沒有複製進來。

## 從唯讀來源檢視確認的系統責任

- Gateway 管理控制面有 Flask UI/API，管理 LiteLLM 原生平台物件；應用推論路徑獨立配置。
- Elasticsearch 聊天流程有 MCP 工具整合和技能設定；來源應用也包含唯讀與可變更狀態的工具。
- OCR 流程包含兩階段處理、Profile 欄位契約、可逆假名化 vault 與稽核流程。
- 原專案有容器及 Helm 部署相關檔案。

以上是從唯讀檢視原始程式和部署檔得知的系統責任，不代表這些私有來源檔包含於本公開 portfolio。

## 本公開 portfolio 包含

- 英文入口 README、繁體中文摘要、三篇案例、系統總覽及交付／範圍說明。
- 依來源模板重建、使用合成資料的離線操作頁面、CSS、JavaScript、架構圖與瀏覽器擷取畫面。
- 以合成資料獨立重建的 Python 範例、測試及其驗證工具。
- 第三方授權聲明與既有 Archify MIT 授權全文。

此清單描述公開 checkout 中實際包含的檔案。上方「從唯讀來源檢視確認的系統責任」則整理原始應用程式與部署檔案呈現的功能；本 checkout 不包含那些私有原始模組。

公開 checkout 未包含一套可檢視的完整來源版 CI/CD pipeline，也未保留部署執行紀錄。因此本頁不列 pipeline 步驟、部署日期、版本狀態或環境驗收結果。這不改變本人已負責相關 CI/CD 與部署工作的說明，只界定讀者能從此檔案直接核實的範圍。

## 讀者可如何查看

1. 從[本機作品集](../index.html)選擇 [Gateway](../demo.html?module=gateway)、[OCR](../demo.html?module=ocr)或 [Elasticsearch 對話](../demo.html?module=chat)示例。
2. 閱讀[Gateway](../case-studies/model-gateway.md)、[OCR](../case-studies/financial-ocr.md)及[Elasticsearch MCP](../case-studies/operations-chatroom.md)案例。
3. 使用[公開示例命令](public-sample.md)執行獨立合成資料範例。

示範能說明設計選擇和重建流程，不證明生產環境狀態、模型品質、交付成效或營運效益。
