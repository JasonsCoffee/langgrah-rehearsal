"""Explicit, opt-in connectivity probe; never runs on import or graph startup."""
import argparse
import json
from pathlib import Path
from .core.ai_models import load_ai_config, ModelClient, ModelError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('ai.local.toml'))
    arguments = parser.parse_args()
    try:
        config = load_ai_config(arguments.config)
    except ModelError as error:
        print(json.dumps({'status':'operational','error':str(error)}), flush=True)
        return 1
    failed = False
    for role in ('coder', 'judge'):
        selected = getattr(config, role)
        record = {'role':role, 'configured_model':selected.model}
        try:
            result = ModelClient(selected, timeout=45).generate(
                'Connection check only. Reply with exactly OK.', max_output_tokens=512)
            record.update(status='connected', returned_model=result.model,
                          input_tokens=result.input_tokens, output_tokens=result.output_tokens,
                          expected_reply=result.text.strip() == 'OK')
        except ModelError as error:
            record.update(status='operational', error=str(error))
            failed = True
        print(json.dumps(record), flush=True)
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
