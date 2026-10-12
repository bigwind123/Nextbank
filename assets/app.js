(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const locale = document.documentElement.lang === 'en' ? 'en' : 'zh';
  const en = locale === 'en';
  const copy = en ? {
    'skip':'Skip to main content','nav.gateway':'AI Model Gateway','nav.ocr':'Financial OCR','nav.chat':'Elasticsearch AIOps','nav.settings':'Connections','offlineLink':'Offline interface example','portfolioLink':'Portfolio home','localOnly':'Local operator console | configured external endpoints receive requests','english':'繁體中文',
    'runtimeTitle':'Local runtime','localBannerTitle':'This operator console runs on the local server.','localBannerBody':'Workspaces, cases, and chats persist in .local/runtime. Browser view state resets when the page reloads.','gateway.title':'AI Model Gateway','gateway.lead':'Manage the local Workspace and model catalog. Approval, native Team selection, and runtime verification remain separate states.','refresh':'Refresh','gateway.provider':'Management provider','gateway.runtime':'Runtime','notVerified':'Not verified','gateway.inference':'Inference endpoint','gateway.workspaces':'Workspace management','gateway.currentWorkspace':'Current Workspace','gateway.workspaceName':'Name','gateway.nativeTeam':'Native Team ID mapping','optional':'optional','gateway.teamHelp':'A native Team ID is needed only when a LiteLLM management endpoint is configured.','saveChanges':'Save changes','delete':'Delete','gateway.addWorkspace':'Add a Workspace','create':'Create','gateway.models':'Model catalog and access','gateway.separation':'Workspace approval records governance only. Select writes to the configured provider. Runtime verification remains unverified.','loading':'Loading…','gateway.modelName':'Model name','gateway.addModel':'Add a model','gateway.timeoutScenario':'Test scenario: apply then return timeout (local registry only)','gateway.timeoutHelp':'Exercise an uncertain result and readback. Confirm the management provider before enabling this scenario.','gateway.operations':'Management operation history','gateway.operation':'Operation','gateway.state':'State','action':'Action','gateway.approve':'Approve','gateway.select':'Select','gateway.reconcile':'Read back','gateway.approved':'Approved','gateway.selected':'Selected','gateway.notApproved':'Not approved','gateway.unknown':'Needs readback','gateway.pending':'Pending','gateway.workspaceMissing':'No Workspace is available. Create one to continue.','gateway.modelMissing':'No model is available. Add one to continue.','gateway.approvalRecorded':'Approval recorded. This does not change Runtime state.','gateway.operationSelected':'Provider state was read back and the selection is confirmed. Runtime remains unverified.','gateway.operationUnknown':'The outcome is unknown. Use readback to reconcile the saved operation.','gateway.reconciled':'Operation state: {state}. Runtime remains unverified.','gateway.reconcileUnknown':'Readback did not confirm the operation. It remains unknown.','gateway.workspaceSaved':'Workspace saved.','gateway.workspaceCreated':'Workspace created.','gateway.workspaceDeleted':'Workspace deleted.','gateway.modelCreated':'Model created.','gateway.modelSaved':'Model name saved.','gateway.modelDeleted':'Model deleted.','gateway.deleteWorkspaceConfirm':'Delete this Workspace? It cannot be deleted after a Gateway operation references it.','gateway.deleteModelConfirm':'Delete this model? It cannot be deleted after a Gateway operation references it.','gateway.providerMode.local_registry':'Local SQLite registry','gateway.providerMode.litellm_management':'LiteLLM management adapter','gateway.providerMode.litellm_management_unconfigured':'LiteLLM management URL set; server-side credential missing','gateway.providerMode.unknown':'Unknown provider mode','gateway.inferenceConfigured':'Model endpoint configured','gateway.inferenceNotConfigured':'No model endpoint configured','gateway.operationId':'ID {id}','gateway.emptyModels':'No models yet. Add a model below.','gateway.emptyOperations':'No management operations yet.','gateway.runtimeControlOnly':'The timeout scenario is disabled because it could trigger a write to the configured LiteLLM Team.','ocr.title':'Financial OCR','ocr.lead':'Upload a PNG or JPEG image for actual recognition. Extracted fields and evaluation results are stored in the local database.','ocr.cases':'Cases','ocr.caseTitle':'Case name','ocr.createCase':'Create case','ocr.selectCase':'Select a case to inspect','ocr.noCase':'Create or select a case to begin.','ocr.caseId':'Case ID','ocr.updated':'Updated','ocr.provider':'Recognition provider','ocr.providerHelp':'RapidOCR runs on local CPU. VLM sends the original image to the vision endpoint you configure.','ocr.vlmConsent':'I understand that the unmasked original image will be sent to my configured endpoint; it is not de-identified before the VLM receives it.','ocr.sampleAlt':'Synthetic application document','ocr.uploadImage':'Choose a PNG or JPEG image','ocr.recognize':'Run recognition and masking','ocr.sampleDoc':'View synthetic sample document','ocr.sampleNote':'This synthetic example image contains no real records.','ocr.recognizedFields':'Recognized fields','ocr.provenance':'Document provenance and masking','ocr.nextRequest':'Next step / outbound profile preview','ocr.savedResponse':'Saved evaluation response','ocr.evaluationMode':'Evaluation mode','ocr.localValidation':'Local schema and field-type checks','ocr.llmEvaluation':'Configured model endpoint','ocr.evalHelp':'Local validation checks field presence and types only; it does not calculate financial formulas or eligibility.','ocr.evaluate':'Run evaluation','ocr.caseCreated':'Case created.','ocr.recognized':'Image recognized and encrypted document record stored.','ocr.evaluated':'Evaluation result stored.','ocr.review':'Needs review','ocr.valid':'Schema checks passed','ocr.providerRapid':'RapidOCR · local CPU','ocr.providerVlm':'Configured vision model','ocr.rapidUnavailable':'OCR is not installed in this runtime. Install requirements-runtime.txt and restart the server.','ocr.llmUnavailable':'Set a model endpoint and vision model name in Connections before using VLM.','ocr.noDocuments':'No recognized documents yet.','ocr.document':'Document','ocr.filename':'File','ocr.providerName':'Provider','ocr.pseudonym':'Pseudonym','ocr.ocrText':'Recognized text','ocr.imageNote':'Only PNG/JPEG images, up to 8 MiB, are accepted.','ocr.selectFile':'Choose an image first.','chat.title':'Elasticsearch AIOps','chat.lead':'Fixed Elasticsearch Ops skill. Search queries the configured index or local FTS; LLM mode is available only after you configure an endpoint.','chat.rooms':'Conversations','chat.createRoom':'Create conversation','chat.roomTitle':'Conversation name','chat.newRoom':'New conversation','chat.selectRoom':'Select or create a conversation','chat.fixedSkill':'Fixed skill','chat.mode':'Response mode','chat.searchMode':'Search index','chat.llmMode':'Configured model','chat.reset':'Clear conversation','chat.export':'Export','chat.empty':'Choose a conversation to search operational events.','chat.message':'Message','chat.messagePlaceholder':'Enter a search query…','chat.send':'Send','chat.user':'You','chat.assistant':'Assistant','chat.results':'{n} matching events · {backend}','chat.noResults':'No matching events were found.','chat.toolCall':'MCP tool call','chat.searchReady':'Local search uses the SQLite FTS5 event index.','chat.elasticsearch':'Search provider: Elasticsearch.','chat.configureLlm':'Configure a model endpoint and model name before selecting LLM mode.','chat.roomCreated':'Conversation created.','chat.messageSent':'Search completed and the returned result is saved.','chat.messageSavedOnly':'The message was saved, but its provider did not complete the response. Review the error and retry if appropriate.','chat.cleared':'Conversation cleared.','chat.exportStarted':'Conversation export is ready.','chat.noRoom':'Create a conversation first.','chat.timestamp':'Time','chat.service':'Service','chat.level':'Level','chat.hitMessage':'Event','settings.title':'Connections','settings.lead':'Only endpoint URLs and model names are saved here. Credentials are never read or returned through this form.','settings.litellm':'LiteLLM management endpoint','settings.modelBase':'OpenAI-compatible model endpoint','settings.modelName':'Chat and evaluation model name','settings.visionName':'OCR VLM model name','settings.esUrl':'Elasticsearch endpoint','settings.secretNote':'Add API keys and LiteLLM management credentials yourself in the ignored .local/runtime-config.json or environment variables. This form has no credential fields and contains no sample credentials.','settings.endpointNote':'When Elasticsearch is unset, search uses local SQLite FTS5 synthetic events. Configuring an external endpoint sends requests to that endpoint.','settings.saved':'Connection settings saved.','settings.providerMode':'Gateway provider: {mode}','settings.secretsLocal':'Credentials are configured server-side and are not returned by the API.','footer':'Local public runtime · SQLite persistence · external providers optional','readme':'Portfolio README','errorPrefix':'Request failed','genericError':'The local runtime could not complete the request.','status.connected':'Runtime connected','status.offline':'Runtime unavailable','unknown':'Unknown','providerError':'Configured provider unavailable','operationState.selected':'Selected','operationState.unknown':'Unknown / needs readback','operationState.pending':'Pending','operationState.failed':'Failed','delete':'Delete'
  } : {};
  const format = (value, vars = {}) => String(value).replace(/\{(\w+)\}/g, (_, name) => vars[name] ?? '');
  const t = (key, vars = {}) => {
    const value = en ? enText[key] : zhText[key];
    return format(value ?? key, vars);
  };
  const zhText = {
    skip:'跳至主要內容','nav.gateway':'AI Model Gateway','nav.ocr':'Financial OCR','nav.chat':'Elasticsearch AIOps','nav.settings':'連線設定',offlineLink:'離線介面示例',portfolioLink:'作品集首頁',localOnly:'本機操作台｜已設定的外部端點會收到請求',english:'English',runtimeTitle:'本機執行環境',localBannerTitle:'此操作台在本機伺服器執行。',localBannerBody:'Workspace、案例與對話會保存於 .local/runtime；瀏覽器檢視狀態在重新載入後重讀。','gateway.title':'AI Model Gateway','gateway.lead':'管理本機 Workspace 與模型目錄，分開記錄核准、原生 Team 選用與執行階段驗證。',refresh:'重新整理','gateway.provider':'管理 provider','gateway.runtime':'Runtime',notVerified:'未驗證','gateway.inference':'推論端點','gateway.workspaces':'Workspace 管理','gateway.currentWorkspace':'目前 Workspace','gateway.workspaceName':'名稱','gateway.nativeTeam':'原生 Team ID 對應',optional:'選填','gateway.teamHelp':'只有設定 LiteLLM 管理端點時，才需要原生 Team ID。',saveChanges:'儲存變更',delete:'刪除','gateway.addWorkspace':'新增 Workspace',create:'建立','gateway.models':'模型目錄與存取','gateway.separation':'Workspace 核准只記錄治理決策；選用會另行寫入設定的 provider。Runtime 狀態保持未驗證。',loading:'載入中…','gateway.modelName':'模型名稱','gateway.addModel':'新增模型','gateway.timeoutScenario':'測試情境：套用後回報逾時（僅本機 registry）','gateway.timeoutHelp':'用於演練未知結果與讀回；切換前請確認管理 provider。','gateway.operations':'管理操作紀錄','gateway.operation':'操作','gateway.state':'狀態',action:'操作','gateway.approve':'核准','gateway.select':'選用','gateway.reconcile':'讀回','gateway.approved':'已核准','gateway.selected':'已選用','gateway.notApproved':'未核准','gateway.unknown':'待讀回','gateway.pending':'處理中','gateway.workspaceMissing':'目前沒有 Workspace，請先建立。','gateway.modelMissing':'目前沒有模型，請先新增。','gateway.approvalRecorded':'已記錄核准。這不會改變 Runtime 狀態。','gateway.operationSelected':'Provider 狀態已讀回，選用已確認。Runtime 仍未驗證。','gateway.operationUnknown':'結果未知。請讀回並核對已保存的操作。','gateway.reconciled':'操作狀態：{state}。Runtime 仍未驗證。','gateway.reconcileUnknown':'讀回尚未確認此操作，狀態仍為未知。','gateway.workspaceSaved':'Workspace 已儲存。','gateway.workspaceCreated':'Workspace 已建立。','gateway.workspaceDeleted':'Workspace 已刪除。','gateway.modelCreated':'模型已建立。','gateway.modelSaved':'模型名稱已儲存。','gateway.modelDeleted':'模型已刪除。','gateway.deleteWorkspaceConfirm':'要刪除此 Workspace 嗎？被 Gateway 操作引用後將無法刪除。','gateway.deleteModelConfirm':'要刪除此模型嗎？被 Gateway 操作引用後將無法刪除。','gateway.providerMode.local_registry':'本機 SQLite registry','gateway.providerMode.litellm_management':'LiteLLM 管理 adapter','gateway.providerMode.litellm_management_unconfigured':'已設定 LiteLLM 管理網址，但伺服器端缺少憑證','gateway.providerMode.unknown':'未知 provider 模式','gateway.inferenceConfigured':'已設定模型端點','gateway.inferenceNotConfigured':'尚未設定模型端點','gateway.operationId':'ID {id}','gateway.emptyModels':'尚無模型，請於下方新增。','gateway.emptyOperations':'尚無管理操作。','gateway.runtimeControlOnly':'已設定 LiteLLM 時，逾時情境可能觸發 Team 寫入，因此停用。','ocr.title':'Financial OCR','ocr.lead':'上傳 PNG 或 JPEG 圖片以執行實際辨識。抽取欄位與評估結果會保存至本機資料庫。','ocr.cases':'案件','ocr.caseTitle':'案件名稱','ocr.createCase':'建立案件','ocr.selectCase':'選擇案件以檢視','ocr.noCase':'建立或選擇案件以開始。','ocr.caseId':'案件 ID','ocr.updated':'更新時間','ocr.provider':'辨識 provider','ocr.providerHelp':'RapidOCR 使用本機 CPU。VLM 會將原始圖片傳送至目前設定的模型端點。','ocr.uploadImage':'選擇 PNG 或 JPEG 圖片','ocr.recognize':'執行辨識與遮罩','ocr.sampleDoc':'檢視合成範例文件','ocr.sampleNote':'這是公開示例提供的合成圖片，不含真實資料。','ocr.recognizedFields':'辨識欄位','ocr.provenance':'文件來源與遮罩','ocr.nextRequest':'\u4e0b\u4e00\u6b65\u8207\u5be6\u969b\u9001\u51fa\u8cc7\u6599\u9810\u89bd','ocr.savedResponse':'已保存的評估回應','ocr.evaluationMode':'評估方式','ocr.localValidation':'本機 schema / 欄位型別檢查','ocr.llmEvaluation':'設定的模型端點','ocr.evalHelp':'本機檢查只驗證欄位存在與型別，不計算財務公式或資格。','ocr.evaluate':'執行評估','ocr.caseCreated':'案件已建立。','ocr.recognized':'圖片辨識完成，文件紀錄已加密保存。','ocr.evaluated':'評估結果已保存。','ocr.review':'需要檢視','ocr.valid':'Schema 檢查通過','ocr.providerRapid':'RapidOCR - 本機 CPU','ocr.providerVlm':'已設定的視覺模型','ocr.vlmConsent':'我了解：VLM 會收到未遮罩的原始圖片，傳送到我設定的端點前不會先去識別化。','ocr.sampleAlt':'合成申請文件','ocr.rapidUnavailable':'此 runtime 未安裝 OCR。請安裝 requirements-runtime.txt 並重新啟動伺服器。','ocr.llmUnavailable':'使用 VLM 前，請在連線設定中設定模型端點與視覺模型名稱。','ocr.noDocuments':'尚無已辨識文件。','ocr.document':'文件','ocr.filename':'檔案','ocr.providerName':'Provider','ocr.pseudonym':'假名代碼','ocr.ocrText':'辨識文字','ocr.imageNote':'只接受 PNG/JPEG 圖片，大小上限為 8 MiB。','ocr.selectFile':'請先選擇圖片。','chat.title':'Elasticsearch AIOps','chat.lead':'固定 Elasticsearch Ops 技能。搜尋會查詢設定的索引或本機 FTS；僅在設定端點後才可選用 LLM 模式。','chat.rooms':'對話列表','chat.createRoom':'建立對話','chat.roomTitle':'對話名稱','chat.newRoom':'新對話','chat.selectRoom':'選擇或建立對話','chat.fixedSkill':'固定技能','chat.mode':'回應方式','chat.searchMode':'索引搜尋','chat.llmMode':'已設定模型','chat.reset':'清除對話','chat.export':'匯出','chat.empty':'選擇對話以搜尋操作事件。','chat.message':'訊息','chat.messagePlaceholder':'輸入搜尋問題…','chat.send':'送出','chat.user':'你','chat.assistant':'助理','chat.results':'{n} 筆符合事件 · {backend}','chat.noResults':'找不到符合的事件。','chat.toolCall':'MCP 工具呼叫','chat.searchReady':'本機搜尋使用 SQLite FTS5 事件索引。','chat.elasticsearch':'搜尋 provider：Elasticsearch。','chat.configureLlm':'選用 LLM 模式前，請設定模型端點與模型名稱。','chat.roomCreated':'對話已建立。','chat.messageSent':'搜尋完成，結果已保存。','chat.messageSavedOnly':'訊息已保存，但 provider 未完成回應。請檢查錯誤後再決定是否重試。','chat.cleared':'對話已清除。','chat.exportStarted':'對話匯出已準備完成。','chat.noRoom':'請先建立對話。','chat.timestamp':'時間','chat.service':'服務','chat.level':'級別','chat.hitMessage':'事件','settings.title':'連線設定','settings.lead':'此處只保存端點網址與模型名稱，不會讀取或回傳憑證。','settings.litellm':'LiteLLM 管理端點','settings.modelBase':'OpenAI-compatible 模型端點','settings.modelName':'聊天與評估模型名稱','settings.visionName':'OCR VLM 模型名稱','settings.esUrl':'Elasticsearch 端點','settings.secretNote':'API key 與 LiteLLM 管理憑證需由你自行設定於已忽略追蹤的 .local/runtime-config.json 或環境變數。此表單沒有憑證欄位，也不包含範例憑證。','settings.endpointNote':'未設定 Elasticsearch 時，搜尋使用本機 SQLite FTS5 合成事件。設定外部端點會將請求送往該端點。','settings.saved':'連線設定已儲存。','settings.providerMode':'Gateway provider：{mode}','settings.secretsLocal':'憑證由伺服器端設定，API 不會回傳。','footer':'本機公開 runtime · SQLite 持久化 · 外部 provider 選用','readme':'作品集 README','errorPrefix':'請求失敗','genericError':'本機 runtime 無法完成此請求。','status.connected':'Runtime 已連線','status.offline':'Runtime 無法連線','unknown':'未知','providerError':'設定的 provider 無法使用','operationState.selected':'已選用','operationState.unknown':'未知／待讀回','operationState.pending':'處理中','operationState.failed':'\u5931\u6557'
  };
  const enText = copy;
  // The language-specific dictionary is declared after the static copy so the
  // same markup and state logic serve both local language routes.
  const setStaticCopy = () => {
    $$('[data-i18n]').forEach(el => {
      const value = t(el.dataset.i18n);
      const textNode = [...el.childNodes].find(n => n.nodeType === Node.TEXT_NODE && n.nodeValue.trim());
      if (textNode) textNode.nodeValue = textNode.nodeValue.replace(textNode.nodeValue.trim(), value);
      else if (el.tagName === 'OPTION' || !el.children.length) el.textContent = value;
    });
    $$('[data-i18n-placeholder]').forEach(el => { el.placeholder = t(el.dataset.i18nPlaceholder); });
    $$('[data-i18n-aria]').forEach(el => { el.setAttribute('aria-label', t(el.dataset.i18nAria)); });
    $$('[data-i18n-alt]').forEach(el => { el.alt = t(el.dataset.i18nAlt); });
    const lang = $('#language-link');
    const query = location.search || '';
    lang.href = (en ? 'app.html' : 'app.en.html') + query;
    lang.setAttribute('hreflang', en ? 'zh-Hant' : 'en');
    lang.lang = en ? 'zh-Hant' : 'en';
    document.title = en ? 'AI Model Gateway · Local Runtime' : 'AI Model Gateway · 本機 Runtime';
  };
  const api = async (path, options = {}) => {
    const response = await fetch(path, { cache: 'no-store', ...options });
    if (response.status === 204) return null;
    const type = response.headers.get('content-type') || '';
    const body = type.includes('application/json') ? await response.json() : await response.text();
    if (!response.ok) {
      const error = body && body.error ? body.error : {};
      const ex = new Error(error.message || `${t('errorPrefix')} (${response.status})`);
      ex.status = response.status; ex.code = error.code || 'request_failed';
      throw ex;
    }
    return body;
  };
  const json = value => ({ method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(value) });
  const state = { health:null, settings:null, settingsBusy:0, workspaces:[], models:[], operations:[], workspaceId:'', cases:[], caseId:'', rooms:[], roomId:'', busy:false };
  const setSettingsBusy = busy => {
    state.settingsBusy = Math.max(0, state.settingsBusy + (busy ? 1 : -1));
    const controls = [...$$('#settings-form input, #settings-form button'), $('#refresh-settings')].filter(Boolean);
    controls.forEach(control => { control.disabled = state.settingsBusy > 0; });
  };
  const showError = error => {
    const banner = $('#global-error');
    banner.textContent = `${t('errorPrefix')}: ${error?.message || t('genericError')}${error?.status ? ` (${error.status})` : ''}`;
    banner.classList.remove('is-hidden');
  };
  const clearError = () => $('#global-error').classList.add('is-hidden');
  const setStatus = (id, message) => { const node = $(id); if (node) node.textContent = message || ''; };
  const setBusy = (button, busy, label) => { if (!button) return; button.disabled = busy; if (label) button.dataset.busyLabel = busy ? label : ''; };
  const run = async (work, statusId) => {
    clearError();
    try { await work(); }
    catch (error) { showError(error); if (statusId) setStatus(statusId, error.message || t('genericError')); throw error; }
  };
  const safeRun = async (work, statusId) => { try { await run(work,statusId); } catch (_) {} };
  const providerLabel = mode => t(`gateway.providerMode.${mode}`) || t('gateway.providerMode.unknown');
  const shortId = id => String(id || '').slice(0,8);
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pretty = value => JSON.stringify(value, null, 2);

  const setView = view => {
    const known = ['gateway','ocr','chat','settings'].includes(view) ? view : 'gateway';
    $$('.view-panel').forEach(el => el.classList.toggle('is-hidden', el.id !== `${known}-view`));
    $$('.nav-link').forEach(el => { const active = el.dataset.view === known; el.classList.toggle('is-active',active); if(active) el.setAttribute('aria-current','page'); else el.removeAttribute('aria-current'); });
    history.replaceState(null,'',`${location.pathname}?view=${known}`);
    if (known === 'gateway') safeRun(refreshGateway);
    if (known === 'ocr') safeRun(refreshCases);
    if (known === 'chat') safeRun(refreshRooms);
    if (known === 'settings') safeRun(refreshSettings);
  };

  async function refreshHealth(){
    state.health = await api('/api/health');
    $('#runtime-mode').textContent = providerLabel(state.health.gateway_provider_mode);
    $('#gateway-provider').textContent = providerLabel(state.health.gateway_provider_mode);
    $('#provider-dot').className = 'status-dot ' + (state.health.gateway_provider_mode === 'litellm_management_unconfigured' ? 'bad-dot' : '');
    $('#inference-state').textContent = state.health.inference_configured ? t('gateway.inferenceConfigured') : t('gateway.inferenceNotConfigured');
    $('#runtime-health').textContent = t('status.connected');
    $('#runtime-health').classList.remove('health-bad');
    if (state.health.ocr_mode === 'not_installed') $('#ocr-provider').disabled = true;
    const timeout = $('#simulate-timeout');
    timeout.disabled = state.health.gateway_provider_mode !== 'local_registry';
    if(timeout.disabled) timeout.checked = false;
    timeout.title = timeout.disabled ? t('gateway.runtimeControlOnly') : '';
  }
  async function refreshSettings(){
    setSettingsBusy(true);
    try{
      const data = await api('/api/settings'); state.settings = data.settings;
      $('#setting-litellm').value = state.settings.litellm_url || '';
      $('#setting-model-base').value = state.settings.model_base_url || '';
      $('#setting-model-name').value = state.settings.model_name || '';
      $('#setting-vision-model').value = state.settings.vision_model_name || '';
      $('#setting-es-url').value = state.settings.es_url || '';
      $('#settings-provider').textContent = t('settings.providerMode',{mode:providerLabel(state.settings.gateway_provider_mode)});
      const llmReady = Boolean(state.settings.model_base_url && state.settings.model_name);
      $('#chat-mode option[value="llm"]').disabled = !llmReady;
      $('#evaluation-mode option[value="llm"]').disabled = !llmReady;
      $('#ocr-provider option[value="vlm"]').disabled = !(state.settings.model_base_url && state.settings.vision_model_name);
    }finally{setSettingsBusy(false);}
  }

  const currentWorkspace = () => state.workspaces.find(w => w.id === state.workspaceId) || null;
  function renderWorkspacePicker(){
    const select=$('#workspace-picker'); select.replaceChildren();
    if(!state.workspaces.length){const opt=document.createElement('option');opt.value='';opt.textContent=t('gateway.workspaceMissing');select.append(opt);select.disabled=true;return;}
    select.disabled=false;
    state.workspaces.forEach(w=>{const opt=document.createElement('option');opt.value=w.id;opt.textContent=w.native_team_id?`${w.name} · ${w.native_team_id}`:w.name;select.append(opt);});
    select.value=state.workspaceId;
    $('#workspace-count').textContent=String(state.workspaces.length);
    const ws=currentWorkspace();
    $('#workspace-name').value=ws?.name||'';$('#workspace-team').value=ws?.native_team_id||'';
  }
  function renderModels(){
    const list=$('#model-list'), ws=currentWorkspace();
    $('#model-count').textContent=String(state.models.length);
    list.replaceChildren();
    if(!state.models.length){const p=document.createElement('p');p.className='empty-note';p.textContent=t('gateway.emptyModels');list.append(p);return;}
    state.models.forEach(model=>{
      const hasUnresolvedOperation=state.operations.some(op=>op.workspace_id===ws?.id&&op.model_id===model.id&&(op.state==='unknown'||op.state==='pending'));
      const card=document.createElement('article');card.className='model-card';
      const header=document.createElement('div');header.className='model-card-head';
      const title=document.createElement('div');const name=document.createElement('span');name.className='model-name';name.textContent=model.name;const id=document.createElement('code');id.className='model-id';id.textContent=model.id;title.append(name,id);
      const badges=document.createElement('div');badges.className='model-badges';
      const approved=Boolean(ws?.approved_model_ids?.includes(model.id));const selected=Boolean(ws?.selected_model_ids?.includes(model.id));
      const approvedTag=document.createElement('span');approvedTag.className='tag '+(approved?'good':'');approvedTag.textContent=approved?t('gateway.approved'):t('gateway.notApproved');badges.append(approvedTag);
      const selectedTag=document.createElement('span');selectedTag.className='tag '+(selected?'neutral':'');selectedTag.textContent=selected?t('gateway.selected'):t('notVerified');badges.append(selectedTag);
      header.append(title,badges);card.append(header);
      const actions=document.createElement('div');actions.className='model-actions';
      const approve=document.createElement('button');approve.type='button';approve.className='button secondary-button';approve.textContent=approved?t('gateway.approved'):t('gateway.approve');approve.disabled=!ws||approved;approve.addEventListener('click',()=>safeRun(async()=>{const b=approve;b.disabled=true;try{await api(`/api/workspaces/${encodeURIComponent(ws.id)}/approve`,json({model_id:model.id}));setStatus('#gateway-status',t('gateway.approvalRecorded'));await refreshGateway();}finally{b.disabled=false;}},'#gateway-status'));
      const select=document.createElement('button');select.type='button';select.className='button primary-button';select.textContent=selected?t('gateway.selected'):t('gateway.select');select.disabled=!ws||!approved||selected||hasUnresolvedOperation;select.addEventListener('click',()=>safeRun(()=>selectModel(ws,model,select),'#gateway-status'));
      const editForm=document.createElement('form');editForm.className='inline-form model-edit';const editInput=document.createElement('input');editInput.className='control';editInput.value=model.name;editInput.maxLength=200;editInput.setAttribute('aria-label',t('gateway.modelName'));editInput.required=true;const save=document.createElement('button');save.type='submit';save.className='button secondary-button';save.textContent=t('saveChanges');const remove=document.createElement('button');remove.type='button';remove.className='button danger-button';remove.textContent=t('delete');
      editForm.append(editInput,save);actions.append(approve,select,remove);card.append(actions,editForm);
      editForm.addEventListener('submit',event=>{event.preventDefault();safeRun(async()=>{save.disabled=true;try{await api(`/api/models/${encodeURIComponent(model.id)}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:editInput.value.trim()})});setStatus('#gateway-status',t('gateway.modelSaved'));await refreshGateway();}finally{save.disabled=false;}},'#gateway-status')});
      remove.addEventListener('click',()=>{if(!confirm(t('gateway.deleteModelConfirm')))return;safeRun(async()=>{remove.disabled=true;try{await api(`/api/models/${encodeURIComponent(model.id)}`,{method:'DELETE'});setStatus('#gateway-status',t('gateway.modelDeleted'));await refreshGateway();}finally{remove.disabled=false;}},'#gateway-status')});
      list.append(card);
    });
  }
  const operationStateLabel = stateName => {
    const key = `operationState.${stateName}`;
    if (stateName === 'selected') return t(key);
    if (stateName === 'unknown') return t(key);
    return t(key) || stateName;
  };
  function renderOperations(){
    const body=$('#operation-rows');body.replaceChildren();
    if(!state.operations.length){const row=document.createElement('tr');const cell=document.createElement('td');cell.colSpan=4;cell.textContent=t('gateway.emptyOperations');row.append(cell);body.append(row);return;}
    state.operations.forEach(op=>{
      const row=document.createElement('tr');
      const id=document.createElement('td');id.textContent=t('gateway.operationId',{id:shortId(op.id)});id.title=op.id;
      const stateCell=document.createElement('td');const badge=document.createElement('span');badge.className='state-pill '+(op.state==='selected'?'selected':op.state==='unknown'?'unknown':'');badge.textContent=operationStateLabel(op.state);stateCell.append(badge);
      const provider=document.createElement('td');provider.textContent=providerLabel(op.provider_mode);
      const action=document.createElement('td');if(op.state==='unknown'||op.state==='pending'){const btn=document.createElement('button');btn.type='button';btn.className='text-button reconcile-button';btn.textContent=t('gateway.reconcile');btn.addEventListener('click',()=>safeRun(()=>reconcileOperation(op,btn),'#gateway-status'));action.append(btn);}else action.textContent='—';
      row.append(id,stateCell,provider,action);body.append(row);
    });
  }
  async function refreshGateway(){
    const [workspaces,models,operations]=await Promise.all([api('/api/workspaces'),api('/api/models'),api('/api/operations')]);
    state.workspaces=workspaces.workspaces||[];state.models=models.models||[];state.operations=operations.operations||[];
    if(!state.workspaces.some(w=>w.id===state.workspaceId))state.workspaceId=state.workspaces[0]?.id||'';
    renderWorkspacePicker();renderModels();renderOperations();
  }
  async function selectModel(ws,model,button){
    button.disabled=true;
    try{
      const request={model_id:model.id,idempotency_key:crypto.randomUUID(),actor_id:'local-operator',simulate_timeout:Boolean($('#simulate-timeout').checked&&state.health?.gateway_provider_mode==='local_registry')};
      const data=await api(`/api/workspaces/${encodeURIComponent(ws.id)}/select`,json(request));
      if(data.operation?.state==='unknown'||data.operation?.state==='pending')setStatus('#gateway-status',t('gateway.operationUnknown'));
      else setStatus('#gateway-status',t('gateway.operationSelected'));
      await refreshGateway();
    }finally{button.disabled=false;}
  }
  async function reconcileOperation(op,button){
    button.disabled=true;
    try{const data=await api(`/api/operations/${encodeURIComponent(op.id)}/reconcile`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});setStatus('#gateway-status',data.confirmed?t('gateway.reconciled',{state:operationStateLabel(data.operation.state)}):t('gateway.reconcileUnknown'));await refreshGateway();}
    finally{button.disabled=false;}
  }
  $('#workspace-picker').addEventListener('change',()=>{state.workspaceId=$('#workspace-picker').value;renderWorkspacePicker();renderModels();});
  $('#workspace-edit-form').addEventListener('submit',event=>{event.preventDefault();const ws=currentWorkspace();if(!ws)return;safeRun(async()=>{await api(`/api/workspaces/${encodeURIComponent(ws.id)}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:$('#workspace-name').value.trim(),native_team_id:$('#workspace-team').value.trim()})});setStatus('#gateway-status',t('gateway.workspaceSaved'));await refreshGateway();},'#gateway-status')});
  $('#workspace-create-form').addEventListener('submit',event=>{event.preventDefault();safeRun(async()=>{const data=await api('/api/workspaces',json({name:$('#new-workspace-name').value.trim(),native_team_id:$('#new-workspace-team').value.trim()}));state.workspaceId=data.workspace.id;$('#workspace-create-form').reset();setStatus('#gateway-status',t('gateway.workspaceCreated'));await refreshGateway();},'#gateway-status')});
  $('#delete-workspace').addEventListener('click',()=>{const ws=currentWorkspace();if(!ws||!confirm(t('gateway.deleteWorkspaceConfirm')))return;safeRun(async()=>{await api(`/api/workspaces/${encodeURIComponent(ws.id)}`,{method:'DELETE'});state.workspaceId='';setStatus('#gateway-status',t('gateway.workspaceDeleted'));await refreshGateway();},'#gateway-status')});
  $('#model-create-form').addEventListener('submit',event=>{event.preventDefault();safeRun(async()=>{await api('/api/models',json({name:$('#new-model-name').value.trim()}));$('#new-model-name').value='';setStatus('#gateway-status',t('gateway.modelCreated'));await refreshGateway();},'#gateway-status')});
  $('#refresh-gateway').addEventListener('click',()=>safeRun(async()=>{await Promise.all([refreshHealth(),refreshGateway()]);setStatus('#gateway-status','');},'#gateway-status'));
  $('#refresh-operations').addEventListener('click',()=>safeRun(refreshGateway,'#gateway-status'));

  function renderCases(){
    const list=$('#case-list');list.replaceChildren();$('#case-count').textContent=String(state.cases.length);
    if(!state.cases.length){const empty=document.createElement('p');empty.className='empty-note';empty.textContent=t('ocr.noCase');list.append(empty);return;}
    state.cases.forEach(item=>{const button=document.createElement('button');button.type='button';button.className='case-row'+(item.id===state.caseId?' is-active':'');button.setAttribute('role','listitem');const title=document.createElement('strong');title.textContent=item.title;const sub=document.createElement('span');sub.textContent=`${item.state} · ${item.document_count} ${en?'documents':'份文件'}`;button.append(title,sub);button.addEventListener('click',()=>safeRun(()=>openCase(item.id),'#ocr-status'));list.append(button);});
  }
  const nullPre = selector => {$(selector).textContent='—';};
  function renderCaseDetail(item){
    $('#case-empty').classList.add('is-hidden');$('#case-workspace').classList.remove('is-hidden');
    $('#case-detail-heading').textContent=item.title;$('#case-state').textContent=item.state;$('#case-id').textContent=item.id;$('#case-updated').textContent=item.updated_at||item.created_at;
    $('#recognized-fields').textContent=item.documents?.length?pretty(item.documents.map(d=>({filename:d.filename,fields:d.fields,provenance:d.provenance}))):t('ocr.noDocuments');
    const docs=$('#document-metadata');docs.replaceChildren();
    if(!item.documents?.length){const p=document.createElement('p');p.className='empty-note';p.textContent=t('ocr.noDocuments');docs.append(p);}else item.documents.forEach(doc=>{
      const entry=document.createElement('article');entry.className='document-entry';const title=document.createElement('strong');title.textContent=`${t('ocr.document')}: ${doc.filename}`;const meta=document.createElement('div');meta.textContent=`${t('ocr.providerName')}: ${doc.provider} · ${t('ocr.pseudonym')}: ${doc.pseudonym}`;const text=document.createElement('details');const summary=document.createElement('summary');summary.textContent=t('ocr.ocrText');const pre=document.createElement('pre');pre.textContent=doc.ocr_text||'—';text.append(summary,pre);entry.append(title,meta,text);docs.append(entry);
    });
    $('#next-request').textContent=pretty({next_step:item.next_request||null,outbound_payload_preview:item.outbound_payload_preview||null});$('#saved-response').textContent=item.saved_response?pretty(item.saved_response):'—';
    const result=$('#evaluation-result');result.classList.add('is-hidden');if(item.saved_response){result.classList.remove('is-hidden');result.classList.toggle('needs-review',item.saved_response.status==='needs_review');const status=item.saved_response.status==='valid'?t('ocr.valid'):t('ocr.review');result.textContent=`${status}\n${pretty(item.saved_response)}`;}
    $('#evaluate-button').disabled=!(item.documents?.length);const llm=$('#evaluation-mode option[value="llm"]');llm.disabled=!(state.settings?.model_base_url&&state.settings?.model_name);
    if(state.health?.ocr_mode==='not_installed'){$('#recognize-button').disabled=true;$('#ocr-status').textContent=t('ocr.rapidUnavailable');}else $('#recognize-button').disabled=false;
    const provider=$('#ocr-provider');const vlm=provider.querySelector('option[value="vlm"]');vlm.disabled=!(state.settings?.model_base_url&&state.settings?.vision_model_name);syncVlmConsent();
  }
  function syncVlmConsent(){const active=$('#ocr-provider').value==='vlm';$('#vlm-consent-row').classList.toggle('is-hidden',!active);if(!active)$('#vlm-consent').checked=false;}
  $('#ocr-provider').addEventListener('change',syncVlmConsent);
  async function refreshCases(){
    const data=await api('/api/ocr/cases');state.cases=data.cases||[];renderCases();
    if(state.caseId&&state.cases.some(c=>c.id===state.caseId))await openCase(state.caseId,false);
    else if(state.cases.length)await openCase(state.cases[0].id,false);
    else {state.caseId='';$('#case-empty').classList.remove('is-hidden');$('#case-workspace').classList.add('is-hidden');$('#case-detail-heading').textContent=t('ocr.selectCase');$('#case-state').textContent='—';}
  }
  async function openCase(id, rerender=true){
    const data=await api(`/api/ocr/cases/${encodeURIComponent(id)}`);state.caseId=id;renderCaseDetail(data.case);if(rerender)renderCases();
  }
  $('#case-create-form').addEventListener('submit',event=>{event.preventDefault();safeRun(async()=>{const title=$('#new-case-title').value.trim();const data=await api('/api/ocr/cases',json({title}));state.caseId=data.case.id;$('#new-case-title').value='';setStatus('#ocr-status',t('ocr.caseCreated'));await refreshCases();},'#ocr-status')});
  $('#upload-form').addEventListener('submit',event=>{event.preventDefault();if($('#ocr-provider').value==='vlm'&&!$('#vlm-consent').checked){setStatus('#ocr-status',t('ocr.vlmConsent'));$('#vlm-consent').focus();return;}const file=$('#ocr-file').files[0];if(!file){setStatus('#ocr-status',t('ocr.selectFile'));return;}const id=state.caseId;if(!id)return;safeRun(async()=>{const button=$('#recognize-button');button.disabled=true;try{const form=new FormData();form.append('file',file,file.name);form.append('provider',$('#ocr-provider').value);const result=await api(`/api/ocr/cases/${encodeURIComponent(id)}/documents`,{method:'POST',body:form});setStatus('#ocr-status',t('ocr.recognized'));await refreshCases();}finally{button.disabled=false;}},'#ocr-status')});
  $('#evaluation-form').addEventListener('submit',event=>{event.preventDefault();if(!state.caseId)return;safeRun(async()=>{const button=$('#evaluate-button');button.disabled=true;try{await api(`/api/ocr/cases/${encodeURIComponent(state.caseId)}/evaluate`,json({mode:$('#evaluation-mode').value}));setStatus('#ocr-status',t('ocr.evaluated'));await refreshCases();}finally{button.disabled=false;}},'#ocr-status')});
  $('#refresh-cases').addEventListener('click',()=>safeRun(refreshCases,'#ocr-status'));

  function renderRooms(){
    const list=$('#room-list');list.replaceChildren();
    if(!state.rooms.length){const empty=document.createElement('p');empty.className='empty-note';empty.textContent=t('chat.noRoom');list.append(empty);return;}
    state.rooms.forEach(room=>{const button=document.createElement('button');button.type='button';button.className='room-item'+(room.id===state.roomId?' is-active':'');button.setAttribute('role','listitem');const title=document.createElement('strong');title.textContent=room.title;const meta=document.createElement('span');meta.textContent=`${room.message_count||0} ${en?'messages':'則訊息'}`;button.append(title,meta);button.addEventListener('click',()=>safeRun(()=>openRoom(room.id),'#chat-status'));list.append(button);});
  }
  function appendToolDetails(parent, call){
    const details=document.createElement('details');const summary=document.createElement('summary');summary.textContent=t('chat.toolCall');const pre=document.createElement('pre');pre.textContent=pretty({name:call.name,arguments:call.arguments,result:call.result});details.append(summary,pre);parent.append(details);
  }
  function renderTranscript(room){
    const transcript=$('#transcript');transcript.replaceChildren();
    if(!room||!room.messages?.length){const empty=document.createElement('div');empty.className='empty-state';const p=document.createElement('p');p.textContent=t('chat.empty');empty.append(p);transcript.append(empty);return;}
    room.messages.forEach((message,index)=>{
      const article=document.createElement('article');article.className=`chat-message ${message.role==='user'?'user':'assistant'}`;
      const role=document.createElement('div');role.className='role-label';role.textContent=message.role==='user'?t('chat.user'):t('chat.assistant');article.append(role);
      if(message.role==='assistant'&&message.mode==='search'){
        let result=message.metadata||{};if(!result.hits){try{result=JSON.parse(message.content);}catch(_){result={};}}
        const summary=document.createElement('p');summary.className='result-summary';summary.textContent=t('chat.results',{n:result.total??0,backend:result.backend||'—'});article.append(summary);
        if(!result.hits?.length){const no=document.createElement('p');no.textContent=t('chat.noResults');article.append(no);}else result.hits.forEach(hit=>{const div=document.createElement('div');div.className='search-hit';const name=document.createElement('strong');name.textContent=hit.service||'—';const messageNode=document.createElement('p');messageNode.textContent=hit.message||'—';const meta=document.createElement('small');meta.textContent=`${hit.level||''} · ${hit.timestamp||''}`;div.append(name,messageNode,meta);article.append(div);});
        const previousUser=room.messages[index-1];const call=room.toolcalls?.find(tc=>tc.name==='es_search'&&tc.arguments?.query===(previousUser?.content||''));if(call)appendToolDetails(article,call);
      }else{const content=document.createElement('div');content.textContent=message.content;article.append(content);if(message.metadata?.toolcalls?.length)message.metadata.toolcalls.forEach(call=>appendToolDetails(article,call));}
      transcript.append(article);
    });
    transcript.scrollTop=transcript.scrollHeight;
  }
  async function openRoom(id){
    const data=await api(`/api/chat/rooms/${encodeURIComponent(id)}`);state.roomId=id;renderRooms();renderTranscript(data.room);$('#conversation-title').textContent=data.room.title;$('#message-input').disabled=false;$('#send-message').disabled=false;$('#reset-room').disabled=false;$('#export-room').disabled=false;
  }
  async function refreshRooms(){
    const data=await api('/api/chat/rooms');state.rooms=data.rooms||[];renderRooms();
    if(state.roomId&&state.rooms.some(r=>r.id===state.roomId))await openRoom(state.roomId);
    else if(state.rooms.length)await openRoom(state.rooms[0].id);
    else{state.roomId='';$('#conversation-title').textContent=t('chat.selectRoom');$('#message-input').disabled=true;$('#send-message').disabled=true;$('#reset-room').disabled=true;$('#export-room').disabled=true;renderTranscript(null);}
    const llm=$('#chat-mode option[value="llm"]');llm.disabled=!(state.settings?.model_base_url&&state.settings?.model_name);
  }
  $('#create-room').addEventListener('click',()=>$('#new-room-title').focus());
  $('#room-create-form').addEventListener('submit',event=>{event.preventDefault();safeRun(async()=>{const title=$('#new-room-title').value.trim()||(en?'Operations chat':'營運對話');const data=await api('/api/chat/rooms',json({title}));state.roomId=data.room.id;$('#new-room-title').value='';setStatus('#chat-status',t('chat.roomCreated'));await refreshRooms();},'#chat-status')});
  $('#message-form').addEventListener('submit',event=>{event.preventDefault();const id=state.roomId;if(!id){setStatus('#chat-status',t('chat.noRoom'));return;}const text=$('#message-input').value.trim();if(!text)return;safeRun(async()=>{const button=$('#send-message');button.disabled=true;try{await api(`/api/chat/rooms/${encodeURIComponent(id)}/messages`,json({message:text,mode:$('#chat-mode').value}));$('#message-input').value='';setStatus('#chat-status',t('chat.messageSent'));await refreshRooms();}catch(error){await openRoom(id);setStatus('#chat-status',t('chat.messageSavedOnly'));throw error;}finally{button.disabled=false;}},'#chat-status')});
  $('#message-input').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();$('#message-form').requestSubmit();}});
  $('#reset-room').addEventListener('click',()=>safeRun(async()=>{const id=state.roomId;if(!id)return;await api(`/api/chat/rooms/${encodeURIComponent(id)}/messages`,{method:'DELETE'});setStatus('#chat-status',t('chat.cleared'));await openRoom(id);},'#chat-status'));
  $('#export-room').addEventListener('click',()=>safeRun(async()=>{const response=await fetch(`/api/chat/rooms/${encodeURIComponent(state.roomId)}/export`,{cache:'no-store'});if(!response.ok)throw new Error(`${t('errorPrefix')} (${response.status})`);const blob=await response.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`chat-${state.roomId}.txt`;document.body.append(a);a.click();a.remove();URL.revokeObjectURL(url);setStatus('#chat-status',t('chat.exportStarted'));},'#chat-status'));
  $('#refresh-rooms').addEventListener('click',()=>safeRun(refreshRooms,'#chat-status'));
  $('#chat-mode').addEventListener('change',()=>{if($('#chat-mode').value==='llm'&&!(state.settings?.model_base_url&&state.settings?.model_name)){setStatus('#chat-status',t('chat.configureLlm'));$('#chat-mode').value='search';}});

  $('#settings-form').addEventListener('submit',event=>{event.preventDefault();safeRun(async()=>{setSettingsBusy(true);try{const body={litellm_url:$('#setting-litellm').value.trim(),model_base_url:$('#setting-model-base').value.trim(),model_name:$('#setting-model-name').value.trim(),vision_model_name:$('#setting-vision-model').value.trim(),es_url:$('#setting-es-url').value.trim()};const data=await api('/api/settings',json(body));state.settings=data.settings;setStatus('#settings-status',t('settings.saved'));await Promise.all([refreshHealth(),refreshSettings()]);}finally{setSettingsBusy(false);}},'#settings-status')});
  $('#refresh-settings').addEventListener('click',()=>safeRun(refreshSettings,'#settings-status'));
  $$('.nav-link').forEach(button=>button.addEventListener('click',()=>setView(button.dataset.view)));

  async function init(){
    setStaticCopy();
    const requested=new URLSearchParams(location.search).get('view')||'gateway';
    const view=['gateway','ocr','chat','settings'].includes(requested)?requested:'gateway';
    try{
      await refreshHealth();await refreshSettings();
      await refreshGateway();
      if(view==='ocr')await refreshCases();if(view==='chat')await refreshRooms();
      $$('.view-panel').forEach(el=>el.classList.toggle('is-hidden',el.id!==`${view}-view`));
      $$('.nav-link').forEach(el=>{const active=el.dataset.view===view;el.classList.toggle('is-active',active);if(active)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});
    }catch(error){$('#runtime-health').textContent=t('status.offline');$('#runtime-health').classList.add('health-bad');showError(error);}
  }
  init();
})();
