import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

// Isolate generator preferences from the developer's global OpenSpec profile.
const configHome = mkdtempSync(join(tmpdir(), 'openspec-refresh-'));
try {
  mkdirSync(join(configHome, 'openspec'));
  writeFileSync(join(configHome, 'openspec', 'config.json'), JSON.stringify({
    profile: 'custom',
    delivery: 'skills',
    workflows: ['propose', 'explore', 'new', 'continue', 'apply', 'update',
      'ff', 'sync', 'archive', 'bulk-archive', 'verify', 'onboard'],
  }));
  const root = fileURLToPath(new URL('../', import.meta.url));
  const result = spawnSync(process.execPath, [
    join(root, 'node_modules', '@fission-ai', 'openspec', 'bin', 'openspec.js'),
    'init', '--tools', 'codex,codebuddy', '--profile', 'custom', '--no-animation',
  ], {
    cwd: root,
    stdio: 'inherit',
    env: { ...process.env, XDG_CONFIG_HOME: configHome, OPENSPEC_TELEMETRY: '0' },
  });
  if (result.error) throw result.error;
  process.exitCode = result.status ?? 1;
} finally {
  rmSync(configHome, { recursive: true, force: true });
}
