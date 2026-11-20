"""One additional Ubuntu 24 slot; recover assigned work before admission checks."""
import ctypes
from ctypes import wintypes
import datetime
import json
import math
import os
from pathlib import Path
import shutil
import time
import controller
import backend

GIB = 1024 ** 3
ROOT = Path(__file__).resolve().parent
SLOT = ROOT / 'slots' / 'ubuntu24-2'
LINUX_PROBE = """import json,os
m={l.split(':')[0]:int(l.split()[1])*1024 for l in open('/proc/meminfo') if ':' in l}
s=os.statvfs('/')
print(json.dumps(dict(available=m['MemAvailable'],disk_free=s.f_bavail*s.f_frsize,cpus=os.cpu_count())))
"""

def event(name, **fields):
    target = SLOT / 'events.jsonl'
    if target.exists() and target.stat().st_size > 2_000_000:
        target.replace(SLOT / 'events.previous.jsonl')
    with target.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                    event=name, **fields)) + '\n')

def stopped():
    if (ROOT / 'STOP').exists() or (SLOT / 'STOP').exists():
        return True
    settings = json.loads(controller.CONFIG.read_text())['parallel_capacity']
    return settings.get('enabled') is not True or settings.get('ubuntu24_workers') != 2

def cpu_load(before, after):
    idle, kernel, user = (b-a for a, b in zip(before, after))
    total = kernel + user
    if total <= 0 or idle < 0 or idle > total:
        raise ValueError('Invalid CPU sample')
    return 100 * (total-idle) / total

def windows_snapshot(paths):
    class Memory(ctypes.Structure):
        _fields_ = [('length', wintypes.DWORD), ('load', wintypes.DWORD)] + [
            (name, ctypes.c_ulonglong) for name in
            ('total', 'available', 'page_total', 'page_available', 'virtual_total', 'virtual_available', 'extended')]
    memory = Memory(); memory.length = ctypes.sizeof(memory)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
        raise OSError('Windows memory probe failed')
    def sample():
        values = [wintypes.FILETIME() for _ in range(3)]
        if not ctypes.windll.kernel32.GetSystemTimes(*(ctypes.byref(v) for v in values)):
            raise OSError('Windows CPU probe failed')
        return [v.dwHighDateTime * 2**32 + v.dwLowDateTime for v in values]
    first = sample(); time.sleep(0.25)
    return dict(available=memory.available, cpus=os.cpu_count(), cpu_percent=cpu_load(first, sample()),
                disk_free=min(shutil.disk_usage(path).free for path in paths))

def sandbox_count(names):
    # An engine and guard are one slot; an uncertain guard-only create reserves it.
    return len({name[len(prefix):] for name in names for prefix in
                ('eagle-fleet-engine-', 'eagle-fleet-guard-') if name.startswith(prefix)})

def admission(config, windows, linux, count):
    settings = config['parallel_capacity']
    if settings.get('enabled') is not True or settings.get('ubuntu24_workers') != 2:
        return False, 'disabled'
    if config['memory_limit'] != '8g':
        return False, 'unsupported-worker-memory'
    for snapshot, fields in ((windows, ('available','cpus','disk_free','cpu_percent')),
                              (linux, ('available','cpus','disk_free'))):
        for field in fields:
            value = snapshot[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError('Invalid resource metric: ' + field)
    if not 0 <= windows['cpu_percent'] <= 100 or min(windows['cpus'], linux['cpus']) < 1:
        raise ValueError('Invalid CPU resources')
    if count >= 2: return False, 'worker-limit'
    # Reserve both full worker budgets, including an empty or partly loaded
    # primary. Conservative double counting avoids relying on reclaimable cache
    # or an uncommitted peer allocation. Floors cannot be weakened by settings.
    if windows['available'] < 20 * GIB: return False, 'windows-memory'
    if linux['available'] < max(10 * GIB, config['minimum_available_bytes']) + 16 * GIB:
        return False, 'linux-memory'
    cpus = min(windows['cpus'], linux['cpus'])
    if cpus < 16 or windows['cpu_percent'] + 400 / cpus > 80:
        return False, 'cpu-reserve'
    if min(windows['disk_free'], linux['disk_free']) < 80 * GIB: return False, 'disk-reserve'
    return True, 'ready'

def capacity(config):
    settings = config['parallel_capacity']
    windows = windows_snapshot(settings.get('host_disk_roots', [ROOT.anchor]))
    linux = json.loads(backend.call(['docker','exec','eagle-fleet-proxy','python3','-c',LINUX_PROBE]).stdout)
    names = backend.call(['docker','ps','--filter','label=eagle.fleet=true','--format','{{.Names}}']).stdout.splitlines()
    allowed, reason = admission(config, windows, linux, sandbox_count(names))
    event('capacity', allowed=allowed, reason=reason, windows=windows, linux=linux, sandboxes=sandbox_count(names))
    return allowed

def ubuntu_config(config):
    result = dict(config)
    result['profiles'] = [p for p in config['profiles'] if any(
        label.lower().startswith('eagle-linux-ubuntu24') for label in p['labels'])]
    return result

def step():
    # Recovery owns this slot only and always precedes STOP or resource gating.
    controller.recover()
    if stopped(): return False
    config = ubuntu_config(json.loads(controller.CONFIG.read_text()))
    if not config['profiles'] or not capacity(config): return True
    candidate = controller.queued(config)
    # Queue scanning may take minutes. Recheck current headroom before creation.
    if candidate and not stopped() and capacity(config):
        controller.execute(candidate, config, drain_requested=stopped)
    return True

def configure_slot():
    SLOT.mkdir(parents=True, exist_ok=True)
    controller.STATE = SLOT / 'state.json'
    controller.event = event

def main():
    import msvcrt
    configure_slot()
    with (SLOT / 'controller.lock').open('a+b') as lock:
        if lock.tell() == 0: lock.write(b'0'); lock.flush()
        lock.seek(0)
        try: msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError: return
        event('controller-started', pid=os.getpid())
        while True:
            try:
                if not step(): return
                seconds = max(60, json.loads(controller.CONFIG.read_text())['poll_seconds'])
            except Exception as error:
                event('retry', reason=type(error).__name__ + ': ' + str(error)[:160])
                seconds = 60
            time.sleep(seconds)

if __name__ == '__main__': main()
