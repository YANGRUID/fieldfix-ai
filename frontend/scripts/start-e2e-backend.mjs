import { existsSync } from 'node:fs';
import { spawn, spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const root = resolve(scriptDirectory, '../..');
const candidates = [
  process.env.FIELDFIX_PYTHON,
  process.platform === 'win32' ? resolve(root, '.venv/Scripts/python.exe') : resolve(root, '.venv/bin/python'),
  process.platform === 'win32' ? resolve(root, 'work/venv/Scripts/python.exe') : resolve(root, 'work/venv/bin/python'),
  process.platform === 'win32' ? 'python' : 'python3',
].filter(Boolean);

const python = candidates.find(candidate => {
  if (candidate.includes('/') && !existsSync(candidate)) return false;
  return spawnSync(candidate, ['-c', 'import fastapi, openai, uvicorn'], {stdio: 'ignore'}).status === 0;
});

if (!python) {
  console.error([
    'FieldFix E2E backend dependencies are missing.',
    `From ${root}, run:`,
    '  python3 -m venv .venv',
    '  .venv/bin/python -m pip install -r backend/requirements.txt',
    'Then rerun: cd frontend && npm run test:e2e',
  ].join('\n'));
  process.exit(1);
}

const port = process.env.FIELDFIX_E2E_API_PORT || '8000';
const child = spawn(python, ['-m', 'uvicorn', 'app.main:app', '--port', port], {
  cwd: resolve(root, 'backend'),
  env: {...process.env, OPENAI_API_KEY: '', DATABASE_PATH: resolve(root, 'work/fieldfix-e2e.db')},
  stdio: 'inherit',
});

for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
child.on('exit', code => process.exit(code ?? 0));
