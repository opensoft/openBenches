"""Prepare changes to openBenches entries in a snapshot of Wave settings."""

from copy import deepcopy
import json
from pathlib import Path
import shlex
import sys


BENCHES = {
    'pyBench': ('pyBench', 'py-bench'),
    'flutterBench': ('flutterBench', 'flutterBench'),
    'cppBench': ('C++Bench', 'C++Bench'),
    'rustBench': ('rustBench', 'rustBench'),
    'cloudBench': ('cloudBench', 'cloudBench'),
}


class MissingTemplate(Exception):
    pass


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def read_object(path):
    try:
        text = path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return {}
    result = json.loads(text, object_pairs_hook=unique_keys) if text else {}
    if not isinstance(result, dict):
        raise ValueError(f'{path.name} must contain a JSON object')
    return result


def write_change(source, updated, path):
    result = json.dumps(updated, indent=2, allow_nan=False)
    if result != json.dumps(source, indent=2, allow_nan=False):
        path.write_text(result + '\n', encoding='utf-8')


def command(root, bench):
    title, target = BENCHES[bench]
    return ['exec', f'{root}/scripts/wave-container-shell.sh',
            '--workbenches-root', root, '--title', title, target]


def metadata(widget):
    return widget['blockdef']['meta']


def managed_bench(widget, key):
    try:
        args = shlex.split(metadata(widget)['cmd:initscript'])
        return len(args) == 7 and args == command(args[3], key) and Path(args[3]).is_absolute()
    except (AttributeError, KeyError, TypeError, ValueError):
        return False


def reconcile(snapshot, output, templates, checkout, projects, connection, inventory):
    states = dict(row.split('\t', 1) for row in inventory.splitlines())
    original_widgets = read_object(snapshot / 'widgets.json')
    original_connections = read_object(snapshot / 'connections.json')
    widgets = deepcopy(original_widgets)
    connections = deepcopy(original_connections)
    settings = connections.setdefault(connection, {})
    if not isinstance(settings, dict):
        raise ValueError(f'Wave connection {connection} must contain a JSON object')
    settings['conn:wshenabled'] = True

    def update_widget(key, fields):
        if key not in widgets:
            if key not in templates:
                raise MissingTemplate(key)
            widgets[key] = templates[key]
        metadata(widgets[key]).update(fields)

    update_widget('defwidget@terminal', {'connection': connection})
    projects_widget = widgets.get('projects')
    if 'projects' not in widgets or (
        isinstance(projects_widget, dict)
        and projects_widget.get('description') == 'Open the WSL projects directory'
    ):
        update_widget('projects', {'connection': connection, 'file': str(Path(projects).resolve())})
    for key in BENCHES:
        if key in widgets and not managed_bench(widgets[key], key):
            continue  # Preserve a user widget that happens to use the same key.
        if states[key] == 'installed':
            update_widget(key, {
                'connection': connection,
                'cmd:cwd': checkout,
                'cmd:initscript': shlex.join(command(checkout, key)),
            })
        else:
            widgets.pop(key, None)

    write_change(original_connections, connections, output / 'connections.json')
    write_change(original_widgets, widgets, output / 'widgets.json')


if __name__ == '__main__':
    snapshot, output, templates = map(Path, sys.argv[1:4])
    try:
        reconcile(snapshot, output, read_object(templates / 'widgets.json'), *sys.argv[4:])
    except MissingTemplate as error:
        if (templates / 'widgets.json').is_file():
            sys.exit(f'Wave installer did not supply widget {error}')
        sys.exit(3)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        sys.exit(f'Wave settings could not be prepared: {error}')
