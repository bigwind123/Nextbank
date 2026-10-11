#!/usr/bin/env node
/** Rebuild the four authored Archify diagrams. Usage: node tools/build_diagrams.mjs <archify-root>. */
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const archifyRoot = process.argv[2];
if (!archifyRoot || !fs.existsSync(path.join(archifyRoot, 'bin', 'archify.mjs'))) {
  console.error('Pass the local Archify package directory containing bin/archify.mjs.');
  process.exit(2);
}
const cli = path.join(path.resolve(archifyRoot), 'bin', 'archify.mjs');
const outDir = path.join(root, 'assets', 'diagrams');
fs.mkdirSync(outDir, { recursive: true });

const n = (id, type, label, sublabel, x, y, tag) => ({
  id, type, label, sublabel, pos: [x, y], size: [170, 78], ...(tag ? { tag } : {}),
});
const e = (id, from, to, label, variant) => ({ id, from, to, ...(label ? { label } : {}), ...(variant ? { variant } : {}) });
const specs = {
  'platform-overview': {
    title: 'Modular AIOps platform overview',
    subtitle: 'Management control plane and application inference paths',
    components: [
      n('operator', 'external', 'Operator', 'browser session', 35, 300),
      n('flask', 'backend', 'Flask manager', 'modular app', 280, 300),
      n('native_admin', 'cloud', 'LiteLLM native API', 'management control plane', 525, 300),
      n('ocr', 'backend', 'Financial OCR', 'separate application flow', 525, 500),
      n('ocr_inference', 'cloud', 'OCR inference', 'configured endpoint', 825, 500),
      n('chat', 'backend', 'Chat skills', 'application inference flow', 525, 100),
      n('chat_inference', 'cloud', 'Chat inference', 'configured endpoint', 825, 100),
    ],
    connections: [
      e('operator_flask', 'operator', 'flask', 'HTTPS', 'emphasis'),
      e('flask_admin', 'flask', 'native_admin', 'management API'),
      e('ocr_inference', 'ocr', 'ocr_inference', 'model request'),
      e('chat_inference', 'chat', 'chat_inference', 'model request'),
    ],
    cards: [
      { dot: 'cyan', title: 'Control plane', items: ['Flask manager calls the native LiteLLM management API', 'The manager does not proxy model inference'] },
      { dot: 'emerald', title: 'Application inference', items: ['OCR and chat use configured inference endpoints', 'Only an on-premises provider keeps that model request local'] },
    ],
  },
  'gateway-recovery': {
    title: 'Gateway publication and recovery',
    subtitle: 'Unknown write outcomes require readback before confirmation',
    components: [
      n('request', 'external', 'Publish request', 'actor + key + payload', 30, 300),
      n('manager', 'backend', 'Flask manager', 'validate and fingerprint', 240, 300),
      n('ledger', 'database', 'Operation ledger', 'key, actor, payload hash', 450, 300),
      n('native', 'cloud', 'Native management API', 'create attempt', 660, 300),
      n('readback', 'backend', 'Readback check', 'native ID + ownership metadata', 870, 300),
      n('active', 'database', 'Confirmed result', 'matching readback only', 1080, 300),
      n('unknown', 'security', 'UNKNOWN', 'timeout / mismatch', 660, 500),
    ],
    connections: [
      e('request_manager', 'request', 'manager', undefined, 'emphasis'),
      e('manager_ledger', 'manager', 'ledger'),
      e('ledger_native', 'ledger', 'native'),
      e('native_readback', 'native', 'readback'),
      e('readback_active', 'readback', 'active'),
      { ...e('native_unknown', 'native', 'unknown', 'timeout', 'dashed'), labelAt: [745, 420] },
      { id: 'unknown_retry', from: 'unknown', to: 'readback', label: 'retry',
        fromSide: 'right', toSide: 'left', via: [[850, 539], [850, 339]], labelAt: [850, 439] },
      { id: 'readback_unknown', from: 'readback', to: 'unknown', label: 'mismatch',
        fromSide: 'right', toSide: 'right', via: [[1060, 339], [1060, 539]], labelAt: [1060, 439], variant: 'dashed' },
    ],
    cards: [
      { dot: 'rose', title: 'Safe replay', items: ['Same key, actor, and payload returns recorded status', 'Changed actor or payload conflicts'] },
      { dot: 'cyan', title: 'Recovery', items: ['Readback failure or mismatch remains UNKNOWN', 'A retry never creates a second native object'] },
    ],
  },
  'financial-ocr': {
    title: 'Financial OCR field protection',
    subtitle: 'Extraction precedes profile-scoped replacement and stage two',
    components: [
      n('document', 'external', 'Fictional document', 'raw image / source text', 35, 300),
      n('stage1', 'cloud', 'Stage 1 extraction', 'configured OCR / VLM endpoint', 260, 300),
      n('validate', 'backend', 'Profile validation', 'published field allowlist', 500, 300),
      n('vault', 'security', 'AES-GCM token map', 'document scope, memory key', 500, 500),
      n('stage2', 'cloud', 'Stage 2 model', 'validated model output', 750, 300),
      n('result', 'backend', 'Application result', 'allowed fields + provenance', 1000, 300),
    ],
    connections: [
      e('document_stage1', 'document', 'stage1', undefined, 'emphasis'),
      e('stage1_validate', 'stage1', 'validate'),
      e('validate_vault', 'validate', 'vault'),
      e('validate_stage2', 'validate', 'stage2'),
      e('stage2_result', 'stage2', 'result'),
    ],
    cards: [
      { dot: 'emerald', title: 'Data boundary', items: ['Unknown fields and raw image/text are excluded from the sample payload', 'An on-premises stage-one provider is required for local image processing'] },
      { dot: 'cyan', title: 'Limits', items: ['Profile rules do not detect every PII type', 'The example does not recalculate business formulas'] },
    ],
  },
  'elasticsearch-mcp': {
    title: 'Skill-scoped Elasticsearch MCP',
    subtitle: 'The public sample checks tool access at list and dispatch time',
    components: [
      n('user', 'external', 'User request', 'fictional query', 35, 300),
      n('skill', 'frontend', 'Skill page', 'selected skill identity', 250, 300),
      n('config', 'database', 'Skill tool config', 'es_* allowlist', 470, 160),
      n('dispatch', 'security', 'Dispatch guard', 'recheck skill + tool', 700, 300),
      n('provider', 'cloud', 'MCP fixture', 'in-memory, offline', 945, 300),
      n('denied', 'backend', 'Denied call', 'provider not invoked', 700, 500),
    ],
    connections: [
      e('user_skill', 'user', 'skill'),
      e('skill_config', 'skill', 'config'),
      e('skill_dispatch', 'skill', 'dispatch', undefined, 'emphasis'),
      e('config_dispatch', 'config', 'dispatch'),
      e('dispatch_provider', 'dispatch', 'provider'),
      e('dispatch_denied', 'dispatch', 'denied', undefined, 'dashed'),
    ],
    cards: [
      { dot: 'cyan', title: 'Tools in the fixture', items: ['es_search · es_esql · es_list_indices', 'es_get_mappings · es_get_shards'] },
      { dot: 'rose', title: 'Scope statement', items: ['Missing configuration exposes no tools in this sample', 'This sample hardens dispatch beyond the original call path'] },
    ],
  },
};

const run = (args) => {
  const result = spawnSync(process.execPath, [cli, ...args], {
    cwd: archifyRoot, encoding: 'utf8', stdio: 'inherit',
    env: { ...process.env, ARCHIFY_UPDATE_CHECK_DISABLED: '1' },
  });
  if (result.status !== 0) throw new Error(`Archify failed (${result.status}): ${args.join(' ')}`);
};

for (const [name, body] of Object.entries(specs)) {
  const specPath = path.join(outDir, `${name}.architecture.json`);
  const htmlPath = path.join(outDir, `${name}.html`);
  const spec = { schema_version: 1, diagram_type: 'architecture', meta: {
    title: body.title, subtitle: body.subtitle, quality_profile: 'showcase', viewBox: [1280, 720],
  }, components: body.components, connections: body.connections, cards: body.cards };
  fs.writeFileSync(specPath, `${JSON.stringify(spec, null, 2)}\n`, 'utf8');
  run(['validate', 'architecture', specPath, '--quality', 'showcase', '--json']);
  run(['deliver', 'architecture', specPath, htmlPath, '--quality', 'showcase', '--json']);
  const svgPath = path.join(outDir, `${name}.svg`);
  const exporter = path.join(root, 'tools', 'export_svgs.py');
  const exportResult = spawnSync(process.env.PYTHON || 'python', [exporter, htmlPath, svgPath], {
    cwd: root, encoding: 'utf8', stdio: 'inherit',
  });
  if (exportResult.status !== 0) throw new Error(`Archify standalone SVG export failed for ${name} (${exportResult.status})`);
}
console.log(`Built ${Object.keys(specs).length} Archify source, HTML, and SVG sets in assets/diagrams.`);
