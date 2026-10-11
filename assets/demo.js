(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const escapeText = (value) => String(value);
  const locale = document.documentElement.lang === 'en' ? 'en' : 'zh';
  const english = locale === 'en';
  const copy = english ? {
    modelCount: (n) => `${n} ${n === 1 ? 'model' : 'models'}`, approvalCount: (n) => `${n} ${n === 1 ? 'approval' : 'approvals'}`,
    approvedPicker: 'Choose an approved model', needApproval: 'Approve a model first', approved: 'Approved', selected: 'Selected', unverified: 'Not verified',
    waiting: 'Choose an approved model.', pending: (model) => `Needs readback: the selection request for ${model} timed out; native Team state is unknown.`,
    approvalRecorded: (workspace, model) => `Approval recorded for ${workspace} · ${model}.`, selectionConfirmed: 'Selected: native Team state was read back; Runtime remains unverified.',
    readbackConfirmed: 'Readback complete: selected in the native Team; Runtime remains unverified.', timeout: 'Needs readback: the selection request timed out; native Team state is unknown.',
    caseTypes: { income: 'Income document', statement: 'Statement summary', generic: 'Document demo' },
    caseStates: { pending: 'Pending', recognized: 'Recognized', evaluated: 'Evaluated' },
    caseCount: (n) => `${n} case${n === 1 ? '' : 's'}`, pageCount: (n) => `${n} page${n === 1 ? '' : 's'}`,
    open: 'Open', stage1Empty: 'Run recognition to show Profile field values.', requestEmpty: 'No synthetic request payload yet.', rawEmpty: 'No saved evaluation response yet.', parserEmpty: 'Run the evaluation to inspect field structure and types.',
    recognizedCount: (n) => `${n} ${n === 1 ? 'document' : 'documents'}`, notEvaluated: 'Not evaluated', evalPrompt: 'After recognition, run the summary evaluation when ready.',
    providerNames: { 'openai-compatible': 'OpenAI-compatible VLM (synthetic)', 'on-prem': 'On-prem VLM (synthetic)' },
    recognizeDone: (provider) => `Synthetic recognition complete with ${provider}; page provenance is retained and masked values use a reversible-code fixture.`,
    evalPending: 'Ready for summary evaluation', evalDone: 'Summary complete', evalNote: 'The synthetic response passed JSON structure and field-type checks.',
    recognizeAgain: 'Recognition refreshed; the previous evaluation response was cleared. Run the summary again if needed.',
    chatRooms: ['Index status summary', 'Query latency review'], newRoom: (n) => `New conversation ${n}`,
    welcome: 'Create or select a conversation, then enter a synthetic query.', fixedOffline: 'Fixed skill · Offline fixture',
    chatReady: 'Local synthetic fixture is ready.', you: 'You', assistant: 'Elasticsearch Ops fixture', toolCall: 'View MCP tool call',
    reply: 'Synthetic search results: the demo-events fixture returned 3 records. This is offline sample data; no Elasticsearch or model service was contacted.',
    chatSent: 'Synthetic reply shown from a local fixture.', modelSelected: (name) => `Selected demo model setting: ${name}.`,
    resetDone: 'Conversation reset; the current room is kept.', exportDone: 'Synthetic conversation exported locally.', exportRoom: 'Room', exportSkill: 'Skill',
    collapsed: 'Expand conversation list', expanded: 'Collapse conversation list', user: 'You', masked: 'Masked'
  } : {
    modelCount: (n) => `${n} 個模型`, approvalCount: (n) => `${n} 筆核准`,
    approvedPicker: '選擇已核准模型', needApproval: '請先核准模型', approved: '已核准', selected: '已選用', unverified: '未驗證',
    waiting: '等待選擇模型', pending: (model) => `待核對：${model} 選用請求逾時；原生 Team 寫入狀態未知。`,
    approvalRecorded: (workspace, model) => `${workspace} · ${model} 已記錄核准。`, selectionConfirmed: '已選用：原生 Team 狀態已讀回；Runtime 仍未驗證。',
    readbackConfirmed: '核對完成：原生 Team 回讀已選用；Runtime 仍未驗證。', timeout: '待核對：選用請求逾時；原生 Team 寫入狀態未知。',
    caseTypes: { income: '收入證明', statement: '帳單摘要', generic: '文件辨識示例' },
    caseStates: { pending: '待處理', recognized: '已辨識', evaluated: '已評估' },
    caseCount: (n) => `${n} 個案例`, pageCount: (n) => `${n} 頁`, open: '開啟',
    stage1Empty: '執行辨識後顯示 Profile 欄位值。', requestEmpty: '尚無待送出的合成 payload。', rawEmpty: '尚無已儲存的評估回應。', parserEmpty: '評估後檢查欄位結構與型別。',
    recognizedCount: (n) => `${n} 個`, notEvaluated: '尚未評估', evalPrompt: '辨識完成後，可明確執行摘要評估。',
    providerNames: { 'openai-compatible': 'OpenAI-compatible VLM（合成示例）', 'on-prem': 'On-prem VLM（合成示例）' },
    recognizeDone: (provider) => `合成辨識完成：${provider} fixture；頁面值附文件來源，遮罩代碼由合成 vault fixture 產生。`,
    evalPending: '待執行摘要評估', evalDone: '摘要已完成', evalNote: '合成回應通過 JSON 結構與欄位型別檢查。',
    recognizeAgain: '辨識資料更新；舊評估回應已清除。若需要摘要，請重新執行評估。',
    chatRooms: ['索引狀態摘要', '查詢延遲觀察'], newRoom: (n) => `新對話 ${n}`,
    welcome: '建立對話後，輸入合成的查詢問題。', fixedOffline: '固定技能 · 離線 fixture',
    chatReady: '本機合成 fixture 已就緒。', you: '你', assistant: 'Elasticsearch Ops fixture', toolCall: '檢視 MCP 工具呼叫',
    reply: '合成搜尋結果：demo-events fixture 回傳 3 筆結果。這是離線示例資料，未連接 Elasticsearch 或模型服務。',
    chatSent: '已使用本機 fixture 顯示合成回覆。', modelSelected: (name) => `已選取合成模型設定：${name}。`,
    resetDone: '對話已重設；目前對話仍保留。', exportDone: '已匯出本機合成對話。', exportRoom: '對話', exportSkill: '技能',
    collapsed: '展開對話清單', expanded: '收合對話清單', user: '你', masked: '已遮罩'
  };
  const moduleName = new URLSearchParams(location.search).get('module');
  const activeModule = ['gateway', 'ocr', 'chat'].includes(moduleName) ? moduleName : 'gateway';
  const pageFile = english ? 'demo.en.html' : 'demo.html';
  const languageLink = $('#language-switch');
  if (languageLink) {
    languageLink.href = `${english ? 'demo.html' : 'demo.en.html'}?module=${activeModule}`;
    languageLink.setAttribute('hreflang', english ? 'zh-Hant' : 'en');
    languageLink.lang = english ? 'zh-Hant' : 'en';
    languageLink.textContent = english ? '繁體中文' : 'English';
    languageLink.setAttribute('aria-label', english ? 'Open this walkthrough in Traditional Chinese' : 'Open this walkthrough in English');
  }
  $$('[data-module-link]').forEach((link) => { link.href = `${pageFile}?module=${link.dataset.moduleLink}`; });
  if (english) {
    const textMap = {
      '跳至主要內容': 'Skip to main content', '依原始模板重建 · 合成資料 · 離線示例': 'Source-derived rebuild · Synthetic data · Offline demo',
      '平台管理示例': 'Platform admin demo', '目前 Workspace': 'Current Workspace', 'Workspace': 'Workspace',
      '模型與授權': 'Models & Access', '成員與權限': 'Members & Access', '此示例未提供': 'Not included in this demo', '平台': 'Platform',
      '分配與限額': 'Allocation & Limits', 'Workspace 管理': 'Workspace administration', '使用量報表': 'Usage reports',
      'Workspace 是本地管理映射；核准後仍須由管理者選用至原生 Team。': 'Workspace is a local management mapping. An administrator must separately select an approved model for the native Team.',
      '管理範圍：Workspace': 'Scope: Workspace', '已選用模型': 'Selected models', '已核准模型': 'Approved model', '顯示已加入原生 Team allowlist 的模型。': 'Models added to the native Team allowlist.',
      '尚未選用模型': 'No models selected', '先在平台頁核准模型，再選用至對應 Team。': 'Approve a model on the Platform page, then select it for the corresponding Team.',
      '模型': 'Model', '原生 Team 狀態': 'Native Team status', 'Runtime': 'Runtime', '選用已核准模型': 'Select an approved model',
      '此操作寫入合成的原生 Team allowlist 狀態。': 'This action writes a synthetic native Team allowlist state.', 'Workspace 操作': 'Workspace action',
      '展示情境：模擬回應逾時': 'Demo scenario: simulate a timeout', '選用': 'Select', '核對': 'Reconcile', '等待選擇模型': 'Choose an approved model.',
      '平台核准、原生 Team 選用與 Runtime 驗證是不同狀態；此示例不連接模型服務。': 'Platform approval, native Team selection, and Runtime verification are separate states. This demo does not connect to a model service.',
      '平台管理範圍': 'Platform admin scope', 'Workspace 模型分配': 'Workspace model allocation',
      '平台 / MODEL ALLOCATION': 'PLATFORM / MODEL ALLOCATION',
      '核准記錄管理決策，不會直接修改原生 Team allowlist。': 'Approval records a governance decision; it does not change the native Team allowlist.', '核准': 'Approve',
      '核准紀錄': 'Approval records', '核准後可回到 Workspace 頁，另行選用。': 'After approval, return to the Workspace page to select the model separately.',
      '尚無核准紀錄': 'No approval records', '選擇 Workspace 與模型後按「核准」。': 'Choose a Workspace and model, then select Approve.', '記錄': 'Record',
      'Workspace 限額': 'Workspace limits', '此重建示例不包含限額設定功能。': 'Limits are not included in this reconstructed demo.', '未提供': 'Not included',
      'RPM 上限': 'RPM limit', 'TPM 上限': 'TPM limit', '費用上限': 'Cost limit',
      '逾時後先呈現「待核對」；核對確認只代表原生 Team 寫入狀態已讀回，Runtime 仍未驗證。': 'A timeout first shows “Needs readback.” Readback confirms only the native Team write state; Runtime remains unverified.',
      '財力文件': 'Financial documents', '作品集': 'Portfolio', '文件案例': 'Cases', '建立合成案例': 'Create synthetic case', '＋ 建立合成案例': '＋ Create synthetic case',
      '搜尋案例': 'Search cases', '案例編號': 'Case ID', '申請類型': 'Request type', '狀態': 'Status', '文件數': 'Documents', '操作': 'Action',
      '案例與文件均為內建合成 fixture；不讀取本機檔案，也不呼叫外部服務。': 'Cases and documents use built-in synthetic fixtures. No local files are read and no external services are called.',
      '← 返回文件案例': '← Back to cases', '案例明細': 'Case details', '案例資訊': 'Case information', '文件辨識示例': 'Document demo',
      '案例評估': 'Case evaluation', '尚未評估': 'Not evaluated', '辨識完成後，可明確執行摘要評估。': 'Run the summary evaluation explicitly after recognition.',
      '執行用戶財力評估摘要': 'Run user financial summary evaluation', '文件辨識與遮罩': 'Document recognition & masking', '合成 fixture': 'Synthetic fixture',
      '文件類型': 'Document type', '收入證明': 'Income document', '帳單摘要': 'Statement summary', '展示 fixture（合成文件）': 'Demo fixture (synthetic document)',
      '執行辨識與遮罩': 'Run recognition and masking', 'Stage 1 由所選 provider fixture 產生合成值；遮罩值使用可還原代碼表示。': 'Stage 1 uses the selected provider fixture to generate synthetic values. Masked values use reversible tokens.',
      '已辨識文件': 'Recognized documents', '文件頁面': 'Document page', '案例評估資料流': 'Case evaluation data flow',
      '辨識結果先產生下一步 payload；儲存回應與 Parser 結果只在明確執行摘要評估後出現。': 'Recognition creates the next-step payload. The saved response and Parser output appear only after you explicitly run the summary evaluation.',
      '擷取 · 遮罩': 'Extract · Mask', 'Profile 欄位值': 'Profile field values', '合成辨識輸出與遮罩後欄位，保留文件與頁面來源。': 'Synthetic extracted and masked fields with document and page provenance.',
      '執行辨識後顯示 Profile 欄位值。': 'Run recognition to show Profile field values.', '輸出 · 檢視': 'Output · Preview', '下一步 Case request': 'Next Case request',
      '依公開欄位設定組成的下一步請求預覽。': 'Preview of the next request assembled from published field rules.', '尚無待送出的合成 payload。': 'No synthetic request payload yet.',
      '評估後 · 儲存': 'After evaluation · Saved', '已儲存 Raw response': 'Saved Raw response', '明確執行摘要評估後產生的合成回應。': 'Synthetic response produced only after explicitly running the summary evaluation.',
      '尚無已儲存的評估回應。': 'No saved evaluation response yet.', '解析 · Parser': 'Parse · Parser', 'Parser 欄位 / errors': 'Parser fields / errors',
      '檢查 JSON 結構與欄位型別，不重新計算財務公式。': 'Checks JSON structure and field types; it does not recalculate financial formulas.',
      '評估後檢查欄位結構與型別。': 'Run evaluation to inspect field structure and types.',
      'On-prem 是可設定的 provider 選項；示例只呈現合成 fixture，無法代表實際文件處理位置。': 'On-prem is a configurable provider option. This synthetic fixture does not represent where a real document would be processed.',
      '新對話': 'New conversation', '固定技能': 'Fixed skill', '選擇對話或建立新對話': 'Select a conversation or start a new one', '重設對話': 'Reset chat', '匯出對話': 'Export chat',
      '建立對話後，輸入合成的查詢問題。': 'Start a conversation, then enter a synthetic search query.', '固定技能 · 離線 fixture': 'Fixed skill · Offline fixture',
      '輸入訊息': 'Enter a message', '送出': 'Send', '請先選擇或建立對話。': 'Select or create a conversation first.', '0 個': '0 documents',
      '合成回覆與 MCP 呼叫紀錄來自本機 fixture。': 'Synthetic replies and MCP call logs come from a local fixture.',
      '內容與隱私說明': 'Content and privacy notes', 'Portfolio README': 'Portfolio README', '↩ 返回作品集': '← Portfolio'
    };
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const textNodes = []; while (walker.nextNode()) textNodes.push(walker.currentNode);
    textNodes.forEach((node) => { const trimmed = node.nodeValue.trim(); if (textMap[trimmed]) node.nodeValue = node.nodeValue.replace(trimmed, textMap[trimmed]); });
    const aria = {
      'a.top-home': 'Return to portfolio home', 'nav.module-nav': 'Module navigation', '.gateway-screen': 'AI Model Gateway walkthrough',
      '.back-button': 'Back to portfolio', '.side-panel': 'Gateway navigation', '.side-nav': 'Management navigation',
      '.ocr-screen': 'Financial OCR walkthrough', '.ocr-home': 'Back to portfolio', '#ocr-search': 'Search cases',
      '.chat-screen': 'Elasticsearch AIOps chat walkthrough', '.chat-sidebar': 'Conversation list', '.sidebar-toggle': 'Collapse conversation list',
      '.chat-input-label': 'Enter a message', '#workspace-main': 'Main content', '.demo-topbar': 'Site header', '.ocr-header nav': 'Financial OCR navigation'
    };
    Object.entries(aria).forEach(([selector, value]) => { const el = $(selector); if (el) el.setAttribute('aria-label', value); });
    $$('.disabled-fields input').forEach((input) => { const label = input.parentElement.firstChild.textContent.trim(); input.setAttribute('aria-label', `${label}: not included in this demo`); });
    const placeholders = { '#ocr-search': 'Search cases', '#chat-input': 'Enter a message. Press Enter to send; Shift+Enter for a new line.' };
    Object.entries(placeholders).forEach(([selector, value]) => { const el = $(selector); if (el) el.placeholder = value; });
    const labelText = (selector, value) => { const el = $(selector); if (!el) return; const node = [...el.childNodes].find((child) => child.nodeType === Node.TEXT_NODE && child.nodeValue.trim()); if (node) node.nodeValue = node.nodeValue.replace(node.nodeValue.trim(), value); };
    labelText('.workspace-label', 'Current Workspace'); labelText('#platform-workspace', 'Workspace'); labelText('#platform-model', 'Model');
    labelText('.check-label', 'Demo scenario: simulate a timeout'); labelText('#ocr-provider', 'VLM Provider'); labelText('#ocr-doctype', 'Document type');
    labelText('#ocr-file-fixture', 'Demo fixture (synthetic document)');
    $('#ocr-provider').options[0].textContent = copy.providerNames['openai-compatible']; $('#ocr-provider').options[1].textContent = copy.providerNames['on-prem'];
    $('#ocr-doctype').options[0].textContent = copy.caseTypes.income; $('#ocr-doctype').options[1].textContent = copy.caseTypes.statement;
    const headerLabels = ['Model', 'Native Team status', 'Runtime', 'Workspace', 'Model', 'Record', 'Case ID', 'Request type', 'Status', 'Documents', 'Action', 'Document type', 'Document page', 'VLM Provider', 'Status'];
    $$('th').forEach((th, index) => { if (headerLabels[index]) th.textContent = headerLabels[index]; });
    $('#chat-model').setAttribute('aria-label', 'Model');
    $('#ocr-case-type').textContent = copy.caseTypes.generic;
  }
  document.body.dataset.module = activeModule;
  $$('.module-screen').forEach((screen) => screen.classList.toggle('is-hidden', screen.id !== `${activeModule}-module`));
  $$('[data-module-link]').forEach((link) => {
    if (link.dataset.moduleLink === activeModule) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });

  // Gateway: approval records and native Team selection are separate fixtures.
  const workspaces = { atlas: 'Workspace Atlas', beacon: 'Workspace Beacon' };
  const models = { 'model-a': 'text-core', 'model-b': 'vision-plus' };
  const approvals = [];
  const selected = [];
  const unknownSelections = new Map();
  const workspacePicker = $('#workspace-picker');
  const approvedPicker = $('#approved-model-picker');
  const renderGateway = () => {
    $('#workspace-name-heading').textContent = workspaces[workspacePicker.value].toUpperCase();
    const visibleSelected = selected.filter((item) => item.workspace === workspacePicker.value);
    $('#workspace-model-count').textContent = copy.modelCount(visibleSelected.length);
    $('#workspace-empty').classList.toggle('is-hidden', visibleSelected.length > 0);
    $('#selected-table-wrap').classList.toggle('is-hidden', visibleSelected.length === 0);
    $('#selected-model-rows').replaceChildren(...visibleSelected.map((item) => {
      const row = document.createElement('tr');
      row.innerHTML = `<td></td><td><span class="status-pill good">${copy.selected}</span></td><td><span class="status-pill neutral">${copy.unverified}</span></td>`;
      row.cells[0].textContent = item.model;
      return row;
    }));
    const visibleApprovals = approvals.filter((item) => item.workspace === workspacePicker.value);
    approvedPicker.replaceChildren();
    const prompt = document.createElement('option'); prompt.value = ''; prompt.textContent = visibleApprovals.length ? copy.approvedPicker : copy.needApproval; approvedPicker.append(prompt);
    visibleApprovals.forEach((item) => { const option = document.createElement('option'); option.value = `${item.workspace}|${item.modelId}`; option.textContent = `${item.model} · ${item.workspaceName}`; approvedPicker.append(option); });
    $('#select-model').disabled = !visibleApprovals.length || [...unknownSelections.keys()].some((key) => key.startsWith(`${workspacePicker.value}|`));
    $('#platform-approval-count').textContent = copy.approvalCount(approvals.length);
    $('#platform-approved-empty').classList.toggle('is-hidden', approvals.length > 0);
    $('#platform-approved-wrap').classList.toggle('is-hidden', approvals.length === 0);
    $('#platform-approved-rows').replaceChildren(...approvals.map((item) => {
      const row = document.createElement('tr'); row.innerHTML = `<td></td><td></td><td><span class="status-pill">${copy.approved}</span></td>`;
      row.cells[0].textContent = item.workspaceName; row.cells[1].textContent = item.model; return row;
    }));
  };
  const gatewayTab = (view) => {
    const workspace = view === 'workspace';
    $('#gw-workspace-view').classList.toggle('is-hidden', !workspace);
    $('#gw-platform-view').classList.toggle('is-hidden', workspace);
    $('#gw-workspace-tab').classList.toggle('is-current', workspace);
    $('#gw-platform-tab').classList.toggle('is-current', !workspace);
    if (workspace) { $('#gw-workspace-tab').setAttribute('aria-current', 'page'); $('#gw-platform-tab').removeAttribute('aria-current'); }
    else { $('#gw-platform-tab').setAttribute('aria-current', 'page'); $('#gw-workspace-tab').removeAttribute('aria-current'); }
  };
  $('#gw-workspace-tab').addEventListener('click', () => gatewayTab('workspace'));
  $('#gw-platform-tab').addEventListener('click', () => gatewayTab('platform'));
  const updateSelectionStatus = () => {
    const pending = [...unknownSelections.values()].find((item) => item.workspace === workspacePicker.value);
    $('#select-model').disabled = !approvedPicker.options.length || approvedPicker.options.length <= 1 || Boolean(pending);
    $('#selection-status').textContent = pending ? copy.pending(pending.model) : copy.waiting;
    $('#reconcile-model').classList.toggle('is-hidden', !pending);
  };
  workspacePicker.addEventListener('change', () => { renderGateway(); updateSelectionStatus(); });
  approvedPicker.addEventListener('change', updateSelectionStatus);
  $('#approve-model').addEventListener('click', () => {
    const workspace = $('#platform-workspace').value, modelId = $('#platform-model').value;
    const exists = approvals.some((a) => a.workspace === workspace && a.modelId === modelId);
    if (!exists) approvals.push({ workspace, workspaceName: workspaces[workspace], modelId, model: models[modelId] });
    $('#approval-feedback').textContent = copy.approvalRecorded(workspaces[workspace], models[modelId]);
    renderGateway();
  });
  $('#select-model').addEventListener('click', () => {
    if (!approvedPicker.value) return;
    const [workspace, modelId] = approvedPicker.value.split('|');
    const item = approvals.find((a) => a.workspace === workspace && a.modelId === modelId);
    if (!item) return;
    const key = `${workspace}|${modelId}`;
    if (unknownSelections.has(key)) return;
    if ($('#timeout-mode').checked) {
      unknownSelections.set(key, item);
      $('#selection-status').textContent = copy.timeout;
      $('#reconcile-model').classList.remove('is-hidden');
      $('#select-model').disabled = true;
      return;
    }
    if (!selected.some((s) => s.workspace === workspace && s.modelId === modelId)) selected.push(item);
    $('#selection-status').textContent = copy.selectionConfirmed;
    $('#reconcile-model').classList.add('is-hidden'); renderGateway();
  });
  $('#reconcile-model').addEventListener('click', () => {
    const pending = [...unknownSelections.entries()].find(([, item]) => item.workspace === workspacePicker.value);
    if (!pending) return;
    const [key, item] = pending;
    if (!selected.some((s) => s.workspace === item.workspace && s.modelId === item.modelId)) selected.push(item);
    unknownSelections.delete(key);
    $('#selection-status').textContent = copy.readbackConfirmed;
    $('#reconcile-model').classList.add('is-hidden'); renderGateway();
  });
  $('#platform-workspace').addEventListener('change', () => { $('#approval-feedback').textContent = ''; });
  renderGateway();

  // OCR: deterministic synthetic fixtures, staged request/response lifecycle.
  const cases = [
    { id: 'DEMO-0001', type: 'income', state: 'pending', docs: 0, recognized: false, evaluated: false, fixture: null },
    { id: 'DEMO-0002', type: 'statement', state: 'pending', docs: 0, recognized: false, evaluated: false, fixture: null }
  ];
  let currentCase = null;
  let recognized = false;
  let evaluated = false;
  const renderCases = () => {
    const query = $('#ocr-search').value.trim().toLowerCase();
    const list = cases.filter((item) => `${item.id} ${copy.caseTypes[item.type]}`.toLowerCase().includes(query));
    $('#ocr-case-count').textContent = copy.caseCount(list.length);
    $('#ocr-case-rows').replaceChildren(...list.map((item) => {
      const row = document.createElement('tr');
      row.innerHTML = '<td></td><td></td><td><span class="status-pill neutral"></span></td><td></td><td><button class="text-button" type="button"></button></td>';
      row.cells[0].textContent = item.id; row.cells[1].textContent = copy.caseTypes[item.type]; row.cells[2].querySelector('span').textContent = copy.caseStates[item.state];
      row.cells[3].textContent = copy.pageCount(item.docs); row.querySelector('button').textContent = copy.open;
      row.querySelector('button').addEventListener('click', () => openCase(item)); return row;
    }));
  };
  const resetPipeline = () => {
    $('#ocr-stage1').textContent = copy.stage1Empty;
    $('#ocr-stage1').classList.add('empty-content');
    $('#ocr-case-request').textContent = copy.requestEmpty; $('#ocr-case-request').classList.add('empty-content');
    $('#ocr-raw-response').textContent = copy.rawEmpty; $('#ocr-raw-response').classList.add('empty-content');
    $('#ocr-parser').textContent = copy.parserEmpty; $('#ocr-parser').classList.add('empty-content');
    $('#recognized-docs').replaceChildren(); $('#recognized-docs-wrap').classList.add('is-hidden');
    $('#recognized-count').textContent = copy.recognizedCount(0); $('#ocr-evaluate').disabled = true;
    $('#ocr-eval-state').textContent = copy.notEvaluated; $('#ocr-eval-note').textContent = copy.evalPrompt;
  };
  const openCase = (item) => {
    currentCase = item; recognized = item.recognized; evaluated = item.evaluated;
    $('#ocr-list-view').classList.add('is-hidden'); $('#ocr-detail-view').classList.remove('is-hidden');
    $('#ocr-case-crumb').textContent = item.id; $('#ocr-case-code').textContent = item.id;
    $('#ocr-case-state').textContent = copy.caseStates[item.state]; $('#ocr-case-type').textContent = copy.caseTypes[item.type]; $('#ocr-doc-count').textContent = copy.recognizedCount(item.docs);
    resetPipeline();
    if (recognized && item.fixture) {
      $('#ocr-provider').value = item.fixture.providerId;
      $('#ocr-doctype').value = item.fixture.docType;
      $('#ocr-file-fixture').value = item.fixture.page;
      showRecognition(item.fixture);
    }
    if (evaluated) showEvaluation();
    $('#ocr-detail-heading').focus?.();
  };
  const showRecognition = (fixture) => {
    const providerId = fixture?.providerId || $('#ocr-provider').value;
    const docType = fixture?.docType || $('#ocr-doctype').value;
    const file = fixture?.page || $('#ocr-file-fixture').value;
    const provider = copy.providerNames[providerId];
    const amount = file === 'page1' ? 84500 : 32800;
    const profile = fixture?.profile || { monthly_income: `NTD ${amount.toLocaleString('en-US')}`, document_reference: '⟦DOC-7F2A⟧', source: { document: currentCase.id, page: file === 'page1' ? 1 : 2 } };
    currentCase.fixture = { providerId, docType, page: file, profile };
    currentCase.docs = 1;
    $('#ocr-doc-count').textContent = copy.recognizedCount(currentCase.docs);
    $('#ocr-stage1').textContent = JSON.stringify(profile, null, 2); $('#ocr-stage1').classList.remove('empty-content');
    const request = { case_id: currentCase.id, profile, schema: 'financial-summary-v1' };
    $('#ocr-case-request').textContent = JSON.stringify(request, null, 2); $('#ocr-case-request').classList.remove('empty-content');
    const tr = document.createElement('tr'); tr.innerHTML = `<td></td><td></td><td></td><td><span class="status-pill good">${copy.masked}</span></td>`;
    tr.cells[0].textContent = $('#ocr-doctype').querySelector(`option[value="${docType}"]`).textContent; tr.cells[1].textContent = file; tr.cells[2].textContent = provider;
    $('#recognized-docs').replaceChildren(tr); $('#recognized-docs-wrap').classList.remove('is-hidden'); $('#recognized-count').textContent = copy.recognizedCount(1);
    $('#ocr-evaluate').disabled = false; $('#ocr-provider-note').textContent = copy.recognizeDone(provider);
    currentCase.recognized = true; currentCase.state = 'recognized'; $('#ocr-case-state').textContent = copy.caseStates[currentCase.state]; $('#ocr-case-type').textContent = copy.caseTypes[currentCase.type]; $('#ocr-eval-state').textContent = copy.evalPending;
  };
  const showEvaluation = () => {
    const amount = Number(String(currentCase.fixture?.profile?.monthly_income || '').replace(/[^0-9.]/g, ''));
    const raw = { status: 'ok', summary: { monthly_income: amount, currency: 'TWD' }, source_case: currentCase.id };
    const parsed = { fields: { monthly_income: { value: amount, type: 'number' }, currency: { value: 'TWD', type: 'string' } }, errors: [] };
    $('#ocr-raw-response').textContent = JSON.stringify(raw, null, 2); $('#ocr-raw-response').classList.remove('empty-content');
    $('#ocr-parser').textContent = JSON.stringify(parsed, null, 2); $('#ocr-parser').classList.remove('empty-content');
    $('#ocr-eval-state').textContent = copy.evalDone; $('#ocr-eval-note').textContent = copy.evalNote;
    currentCase.evaluated = true; currentCase.state = 'evaluated'; $('#ocr-case-state').textContent = copy.caseStates[currentCase.state];
  };
  $('#ocr-create-case').addEventListener('click', () => {
    const n = cases.length + 1; const item = { id: `DEMO-${String(n).padStart(4, '0')}`, type: 'generic', state: 'pending', docs: 0, recognized: false, evaluated: false, fixture: null };
    cases.unshift(item); renderCases(); openCase(item);
  });
  $('#ocr-search').addEventListener('input', renderCases);
  $('#ocr-back').addEventListener('click', () => { $('#ocr-detail-view').classList.add('is-hidden'); $('#ocr-list-view').classList.remove('is-hidden'); renderCases(); $('#ocr-create-case').focus(); });
  $('#ocr-recognize').addEventListener('click', () => { if (!currentCase) return; recognized = true; evaluated = false; currentCase.evaluated = false; resetPipeline(); showRecognition(); $('#ocr-provider-note').textContent = copy.recognizeAgain; });
  $('#ocr-evaluate').addEventListener('click', () => { if (!recognized || !currentCase) return; evaluated = true; showEvaluation(); });
  renderCases();

  // Chat: fixed skill context and local fixture; no model/network invocation.
  const rooms = [{ id: 'room-1', name: copy.chatRooms[0], messages: [] }, { id: 'room-2', name: copy.chatRooms[1], messages: [] }];
  let activeRoom = null;
  const renderRooms = () => {
    $('#room-list').replaceChildren(...rooms.map((room) => {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'room-item'; button.setAttribute('role', 'listitem');
      if (activeRoom === room) button.setAttribute('aria-current', 'true'); button.textContent = room.name;
      button.addEventListener('click', () => activateRoom(room)); return button;
    }));
  };
  const welcome = () => `<div class="chat-welcome"><span class="welcome-mark" aria-hidden="true">◈</span><h2>Elasticsearch Operations</h2><p>${copy.welcome}</p><small>${copy.fixedOffline}</small></div>`;
  const activateRoom = (room) => {
    activeRoom = room; $('#chat-room-title').textContent = room.name;
    $('#chat-input').disabled = false; $('#chat-send').disabled = false;
    $('#reset-chat').disabled = false; $('#export-chat').disabled = false;
    $('#chat-status').textContent = copy.chatReady;
    renderRooms(); renderTranscript(); $('#chat-input').focus();
  };
  const renderTranscript = () => {
    if (!activeRoom || activeRoom.messages.length === 0) { $('#chat-transcript').innerHTML = welcome(); return; }
    $('#chat-transcript').replaceChildren(...activeRoom.messages.map((message) => {
      const article = document.createElement('article'); article.className = `chat-message ${message.role}`;
      const role = document.createElement('div'); role.className = 'message-role'; role.textContent = message.role === 'user' ? copy.you : copy.assistant;
      const body = document.createElement('div'); body.textContent = message.text; article.append(role, body);
      if (message.tool) { const details = document.createElement('details'); details.className = 'tool-details'; const summary = document.createElement('summary'); summary.textContent = copy.toolCall; const pre = document.createElement('pre'); pre.textContent = JSON.stringify(message.tool, null, 2); details.append(summary, pre); article.append(details); }
      return article;
    }));
    $('#chat-transcript').scrollTop = $('#chat-transcript').scrollHeight;
  };
  const sendChat = () => {
    if (!activeRoom) return;
    const text = $('#chat-input').value.trim(); if (!text) return;
    activeRoom.messages.push({ role: 'user', text });
    const tool = { jsonrpc: '2.0', method: 'tools/call', params: { name: 'es_search', arguments: { index: 'demo-events', query: text } }, backend_tool: 'search', fixture: true };
    activeRoom.messages.push({ role: 'assistant', text: copy.reply, tool });
    $('#chat-input').value = ''; $('#chat-status').textContent = copy.chatSent; renderTranscript(); $('#chat-input').focus();
  };
  $('#new-room').addEventListener('click', () => {
    const room = { id: `room-${Date.now()}`, name: copy.newRoom(rooms.length + 1), messages: [] }; rooms.unshift(room); activateRoom(room);
  });
  $('#chat-composer').addEventListener('submit', (event) => { event.preventDefault(); sendChat(); });
  $('#chat-input').addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); sendChat(); } });
  $('#chat-model').addEventListener('change', () => { $('#chat-status').textContent = copy.modelSelected($('#chat-model').selectedOptions[0].textContent); });
  $('#reset-chat').addEventListener('click', () => { if (!activeRoom) return; activeRoom.messages = []; renderTranscript(); $('#chat-status').textContent = copy.resetDone; $('#chat-input').focus(); });
  $('#export-chat').addEventListener('click', () => {
    if (!activeRoom) return;
    const body = activeRoom.messages.map((m) => `${m.role === 'user' ? copy.user : 'Assistant'}: ${m.text}`).join('\n\n');
    const blob = new Blob([`${copy.exportRoom}: ${activeRoom.name}\n${copy.exportSkill}: Elasticsearch Ops\n\n${body}\n`], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = `${activeRoom.id}-synthetic.txt`; link.click(); URL.revokeObjectURL(url);
    $('#chat-status').textContent = copy.exportDone;
  });
  $('#chat-sidebar-toggle').addEventListener('click', () => {
    const sidebar = $('#chat-sidebar'), collapsed = sidebar.classList.toggle('is-collapsed');
    $('.chat-screen').classList.toggle('sidebar-collapsed', collapsed);
    $('#chat-sidebar-toggle').setAttribute('aria-expanded', String(!collapsed));
    $('#chat-sidebar-toggle').setAttribute('aria-label', collapsed ? copy.collapsed : copy.expanded);
  });
  if (matchMedia('(max-width: 720px)').matches) {
    $('#chat-sidebar').classList.add('is-collapsed');
    $('.chat-screen').classList.add('sidebar-collapsed');
    $('#chat-sidebar-toggle').setAttribute('aria-expanded', 'false');
    $('#chat-sidebar-toggle').setAttribute('aria-label', copy.collapsed);
  }
  renderRooms();
})();
