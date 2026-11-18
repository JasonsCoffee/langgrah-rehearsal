"""Explicit dedicated-host visual preparation; selectors are environment inputs."""
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from unity_coder.adapters.unity.transport import BridgeTransport, local_http
from unity_coder.core.verification import VerificationRequest

HOST = Path(os.environ['UNITY_HOST']).resolve()
GAME = HOST / 'Assets/JJGame/monopoly'
PORT = int(os.environ.get('UNITY_BRIDGE_PORT', '49166'))
OUTPUT = HOST / '.agent/visual-baseline'
SOURCE = Path(__file__).resolve().parents[2]
TESTS = tuple('FrameworkVisualDemo.Tests.Preparation.' + name for name in (
    'PrefabHasNoMissingScriptsAndAllExplicitBindingsResolve',
    'PlaceholderImportsWithArtistDimensionsAndStableSpriteIdentity',
    'ReviewSceneLoadsItsPrefabWithoutGameBootstrap'))


def command(name: str, **args: object) -> dict[str, object]:
    health = local_http(PORT, 'GET', '/', None, 5)
    if Path(str(health.get('projectPath'))).resolve() != HOST:
        raise ValueError('Wrong Unity host')
    reply = local_http(PORT, 'POST', '/execute', {'command': name, **args}, 30)
    if reply.get('taskId'):
        for _ in range(60):
            time.sleep(1)
            reply = local_http(PORT, 'GET', '/task/' + str(reply.get('taskId')), None, 5)
            if reply.get('status') not in ('pending', 'running', 'queued'):
                break
    return reply


def refresh() -> None:
    command('RefreshAssetDatabase')
    for _ in range(60):
        time.sleep(1)
        try:
            result = command('FrameworkVerifyCapabilities')
            data = json.loads(str(result.get('data', '{}')))
            if data.get('ready') and not data.get('active_ticket'):
                time.sleep(2)
                return
        except (OSError, ValueError):
            continue
    raise TimeoutError('Editor reload did not settle')


def copy_new(source: Path, relative: str) -> None:
    destination = GAME / relative
    data = source.read_bytes()
    if destination.exists() and destination.read_bytes() != data:
        raise ValueError('Refusing to overwrite a different existing file: ' + relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    action = sys.argv[1]
    if action == 'install-tests':
        before = OUTPUT / 'original-files.json'
        if not before.exists():
            names = subprocess.check_output(['git','ls-files','-z'], cwd=GAME).decode().split('\0')
            hashes = {name:sha256((GAME/name).read_bytes()).hexdigest() for name in names if name and (GAME/name).is_file()}
            before.write_text(json.dumps(hashes, indent=2))
        copy_new(SOURCE/'examples/visual_baseline/VisualBaselineTests.cs', 'Tests/Runtime/Script/FrameworkVisualDemo/VisualBaselineTests.cs')
        refresh()
    elif action in ('red', 'green', 'compile'):
        worker = BridgeTransport(HOST, ports=(PORT,), timeout=180)
        report_file = OUTPUT/'editor-report.json'
        revision = sha256(report_file.read_bytes()).hexdigest() if report_file.exists() else 'missing-baseline'
        request = VerificationRequest('visual-baseline-'+action+'-'+revision[:12], 'visual-baseline-v1', 1,
            'isolated-preparation', revision, 'preparation', 'target-profile',
            'dedicated-host', TESTS, True)
        result = worker.compile(request) if action == 'compile' else worker.run_tests(request)
        (OUTPUT/(action+'.json')).write_text(json.dumps(asdict(result), indent=2))
        if result.tests is not None:
            print(json.dumps({'executed': result.tests.executed, 'passed': result.tests.passed,
                'failed': result.tests.failed, 'operational_error': result.tests.operational_error}))
        else:
            print(json.dumps(asdict(result.compilation)))
    elif action == 'install':
        copy_new(SOURCE/'examples/visual_baseline/ExpeditionPreviewShell.cs', 'Runtime/Script/FrameworkVisualDemo/ExpeditionPreviewShell.cs')
        copy_new(SOURCE/'examples/visual_baseline/design.md', 'Editor/ArtSource~/FrameworkVisualDemo/design.md')
        copy_new(SOURCE/'unity/Editor/FrameworkVisualPreparation.cs', 'Editor/Script/FrameworkVisualPreparation/FrameworkVisualPreparation.cs')
        copy_new(SOURCE/'unity/Editor/Framework.Presentation.Editor.asmdef', 'Editor/Script/FrameworkVisualPreparation/Framework.Presentation.Editor.asmdef')
        refresh()
    elif action == 'check-originals':
        hashes = json.loads((OUTPUT/'original-files.json').read_text())
        changed = [name for name, digest in hashes.items() if not (GAME/name).is_file() or sha256((GAME/name).read_bytes()).hexdigest()!=digest]
        print(json.dumps({'tracked_files':len(hashes), 'changed':changed}))
        if changed:
            raise ValueError('Original game content drifted')
    else:
        reply = command('FrameworkPrepareVisual', operation=action)
        if reply.get('status') != 'success':
            raise ValueError(str(reply))
        report = json.loads(str(reply['data']))
        print(json.dumps({key:report[key] for key in ('revision','launchable','missing_scripts','unresolved_bindings','entries')}))


if __name__ == '__main__':
    main()
