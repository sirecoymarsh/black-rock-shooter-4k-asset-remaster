"""Apply the UI checkpoint to a closed, hash-matching combined test bundle.

Default: read-only preflight. --apply: back up, patch ISO, merge exact UI keys.
Python 3.10+, standard library only. See README.md for rollback instructions.
"""
from pathlib import Path
import argparse, base64, configparser, datetime, hashlib, json, os, re, shutil, zlib


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text('utf-8-sig'))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def ini(text):
    c = configparser.ConfigParser(interpolation=None, strict=True)
    c.read_string(text)
    return c


def inside(root, relative):
    path = (root / relative).resolve()
    need(path.is_relative_to(root.resolve()), 'Path escapes root: ' + relative)
    return path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('release', type=Path)
    p.add_argument('--checkpoint', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--apply', action='store_true')
    a = p.parse_args()
    root, release = a.checkpoint.resolve(), a.release.resolve()
    overlay = root / 'ready-ui-overlay'
    m, patch = read(overlay / 'manifest.json'), read(root / 'title-v2-xor-patch.json')
    sourcepack = overlay / 'PSP/TEXTURES/NPUH10126'
    destpack = release / 'memstick/PSP/TEXTURES/NPUH10126'
    iso = release / 'BRS_4K_combined_test.iso'
    manifest_path = release / 'build-manifest.json'
    old_manifest_bytes = manifest_path.read_bytes()
    build = json.loads(old_manifest_bytes)
    need(iso.stat().st_size == patch['size'], 'ISO size differs')
    need(sha(iso) == patch['source_sha256'] == build['iso_sha256'], 'Unsupported ISO hash')
    bindings = m['bindings']
    files = m['files']
    need(set(bindings.values()) == set(files), 'Overlay file allowlist mismatch')
    for rel, meta in files.items():
        src, dst = inside(sourcepack, rel), inside(destpack, rel)
        need(sha(src) == meta['sha256'] and src.stat().st_size == meta['bytes'], rel)
        need(not dst.exists() or sha(dst) == meta['sha256'], 'Existing asset conflict: ' + rel)
    fragment = ini((sourcepack / 'textures-fragment.ini').read_text('utf-8-sig'))
    need(dict(fragment['hashes']) == bindings, 'Fragment differs from manifest')
    ini_path = destpack / 'textures.ini'
    old_ini = ini_path.read_bytes()
    text = old_ini.decode('utf-8-sig')
    old_config = ini(text)
    need(old_config['options']['hash'] == 'xxh64', 'Unsupported hash mode')
    old_bindings = dict(old_config['hashes'])
    protected = {rel: sha(inside(destpack, rel)) for rel in set(old_bindings.values())}
    # Replace only exact [hashes] entries, preserving unrelated sections and lines.
    lines, output, section, pending = text.splitlines(keepends=True), [], '', dict(bindings)
    newline = '\r\n' if '\r\n' in text else '\n'
    for line in lines:
        header = re.match(r'^\s*\[([^]]+)\]', line)
        if header:
            if section == 'hashes':
                output.extend(f'{k} = {v}{newline}' for k, v in sorted(pending.items()))
                pending.clear()
            section = header[1].lower()
        entry = re.match(r'^\s*([0-9a-fA-F]{24})\s*=', line) if section == 'hashes' else None
        if entry and entry[1].lower() in pending:
            k = entry[1].lower()
            line = f'{k} = {pending.pop(k)}{newline}'
        output.append(line)
    if pending:
        need(section == 'hashes', 'Hash section not found')
        if output and not output[-1].endswith(('\n', '\r')):
            output[-1] += newline
        output.extend(f'{k} = {v}{newline}' for k, v in sorted(pending.items()))
    merged = ''.join(output)
    new_config = ini(merged)
    need(dict(new_config['hashes']) == {**old_bindings, **bindings}, 'Unexpected key changes')
    for name in old_config.sections():
        if name != 'hashes':
            need(dict(new_config[name]) == dict(old_config[name]), 'Settings changed')
    chunks, previous_end = [], 0
    for chunk in patch['ranges']:
        offset, length = chunk['offset'], chunk['length']
        need(0 <= previous_end <= offset and offset + length <= patch['size'], 'Bad patch range')
        raw = zlib.decompress(base64.b64decode(chunk['xor_zlib_base64'], validate=True))
        need(len(raw) == length, 'Patch length differs')
        chunks.append((offset, raw))
        previous_end = offset + length
    report = dict(schema='brs-ui-checkpoint-install/v1', release=str(release),
                  overlay_keys=len(bindings), overlay_pngs=len(files),
                  previous_total_keys=len(old_bindings), total_keys=len(new_config['hashes']),
                  source_iso_sha256=patch['source_sha256'], target_iso_sha256=patch['target_sha256'],
                  installed=False, runtime_verified=False, translator_model='Codex internal')
    if not a.apply:
        print(json.dumps(report, ensure_ascii=False))
        return
    need(shutil.disk_usage(release).free > patch['size'] * 2 + 100000000, 'Insufficient backup space')
    backup = release / ('ui-backups/icons-ko-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    temp = release / 'BRS_UI_icons_ko.installing.iso'
    need(not temp.exists(), 'Stale temporary ISO exists')
    shutil.copy2(iso, backup / iso.name)
    (backup / 'textures.ini').write_bytes(old_ini)
    (backup / 'build-manifest.json').write_bytes(old_manifest_bytes)
    created = []
    mutated_bundle = False
    try:
        shutil.copy2(iso, temp)
        with temp.open('r+b') as f:
            for offset, mask in chunks:
                f.seek(offset)
                old = f.read(len(mask))
                need(len(old) == len(mask), 'Truncated input')
                f.seek(offset)
                f.write(bytes(x ^ y for x, y in zip(old, mask)))
        need(sha(temp) == patch['target_sha256'], 'Patched ISO hash differs')
        for rel, meta in files.items():
            dst = inside(destpack, rel)
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                created.append(dst)
                shutil.copy2(inside(sourcepack, rel), dst)
        # Fail closed if another process changed the bundle during preparation.
        need(ini_path.read_bytes() == old_ini and manifest_path.read_bytes() == old_manifest_bytes,
             'Bundle changed concurrently')
        need(sha(iso) == patch['source_sha256'], 'ISO changed concurrently')
        need(all(sha(inside(destpack, rel)) == h for rel, h in protected.items()), 'Existing texture changed')
        mutated_bundle = True
        os.replace(temp, iso)
        ini_path.write_bytes(merged.encode('utf-8'))
        build['iso_sha256'] = patch['target_sha256']
        build['iso_source'] = str(root / 'title-v2-xor-patch.json')
        build['total_keys'] = len(new_config['hashes'])
        build['ui_font_keys_before_icons_ko'] = build.get('ui_font_keys')
        build['ui_font_keys'] = sum(not v.startswith('materials/') for v in new_config['hashes'].values())
        build['ui_icons_ko_checkpoint'] = dict(checkpoint=root.name, keys=len(bindings), pngs=len(files),
                                             installed=True, runtime_verified=False, backup=str(backup))
        write(manifest_path, build)
        need(all(sha(inside(destpack, rel)) == meta['sha256'] for rel, meta in files.items()), 'Installed asset differs')
        need(all(sha(inside(destpack, rel)) == h for rel, h in protected.items()), 'Prior texture changed')
        report.update(installed=True, backup=str(backup), previous_pngs_preserved=len(protected),
                      ini_sha256=sha(ini_path), unchanged_non_ui_keys=len(set(old_bindings) - set(bindings)),
                      created_files=[str(x.relative_to(destpack)) for x in created])
        write(backup / 'installation.json', report)
        write(release / 'ui-icons-ko-installation.json', report)
    except Exception:
        if mutated_bundle:
            shutil.copy2(backup / iso.name, iso)
            ini_path.write_bytes(old_ini)
            manifest_path.write_bytes(old_manifest_bytes)
        for path in created:
            path.unlink(missing_ok=True)
        raise
    finally:
        temp.unlink(missing_ok=True)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
