#!/usr/bin/env python3
"""Extract Takoboto.dll from an intact .NET Android assembly store."""
import argparse, hashlib, json, struct, zipfile
from pathlib import Path
import lz4.block

def extract_store(blob, output):
    base = blob.find(b'XABA')
    if base < 0:
        raise ValueError('No .NET XABA assembly store header')
    count, idxcount, indexsize = struct.unpack_from('<III', blob, base + 8)
    if not 0 < count < 3000 or indexsize > 500_000:
        raise ValueError('Unreasonable XABA header values')
    start = base + 20 + indexsize
    names_pos = start + 28 * count
    entries = [struct.unpack_from('<7I', blob, start + j * 28) for j in range(count)]
    names = []
    for j in range(count):
        size = struct.unpack_from('<I', blob, names_pos)[0]
        names_pos += 4
        names.append(blob[names_pos:names_pos + size].decode('utf-8'))
        names_pos += size
    candidates = [e for n, e in zip(names, entries) if n == 'Takoboto.dll']
    if len(candidates) != 1:
        raise ValueError(f'Takoboto.dll expected once, found {len(candidates)}')
    _, off, size, *_ = candidates[0]
    raw = blob[base + off:base + off + size]
    if len(raw) != size:
        raise ValueError('Takoboto.dll extends past store')
    if raw[:4] == b'XALZ':
        expected = struct.unpack_from('<I', raw, 8)[0]
        if not 10000 < expected < 100_000_000:
            raise ValueError('Invalid uncompressed assembly size')
        dll = lz4.block.decompress(raw[12:], uncompressed_size=expected)
    elif raw[:2] == b'MZ':
        dll = raw
    else:
        raise ValueError('App DLL missing/corrupt; header: ' + raw[:16].hex())
    if dll[:2] != b'MZ' or b'BSJB' not in dll:
        raise ValueError('Not a valid managed .NET assembly')
    output.mkdir(parents=True, exist_ok=True)
    path = output / 'Takoboto.dll'
    path.write_bytes(dll)
    # Cecil resolves app types against the complete set of managed Android dependencies.
    # Extract assemblies next to the app DLL; each XALZ header carries the original size.
    deps = output / 'managed_dependencies'
    deps.mkdir(exist_ok=True)
    written = 0
    for asm_name, entry in zip(names, entries):
        _, pos, length, *_ = entry
        chunk = blob[base + pos:base + pos + length]
        if len(chunk) != length:
            continue
        try:
            if chunk[:4] == b'XALZ':
                original_length = struct.unpack_from('<I', chunk, 8)[0]
                data = lz4.block.decompress(chunk[12:], uncompressed_size=original_length)
            elif chunk[:2] == b'MZ':
                data = chunk
            else:
                continue
            if data[:2] == b'MZ' and b'BSJB' in data:
                (deps / Path(asm_name).name).write_bytes(data)
                written += 1
        except Exception as e:
            print('WARNING dependency extraction', asm_name, str(e))
    print('EXTRACTED managed dependency assemblies:', written)
    info = {'assembly_count': count, 'managed_dll': str(path),
            'managed_bytes': len(dll), 'sha256': hashlib.sha256(dll).hexdigest(),
            'names': names}
    (output / 'assembly_inventory.json').write_text(json.dumps(info, indent=2))
    return info

def main():
    p = argparse.ArgumentParser()
    p.add_argument('apk')
    p.add_argument('--output', default='recovered')
    args = p.parse_args()
    output = Path(args.output)
    with zipfile.ZipFile(args.apk) as z:
        stores = [n for n in z.namelist()
                  if n.endswith('/libassembly-store.so') or n == 'libassembly-store.so']
        if not stores:
            raise SystemExit('No assembly store in APK; check ABI split')
        failures = []
        for name in stores:
            try:
                data = z.read(name)
                info = extract_store(data, output)
                print('RECOVERED', info['managed_dll'], info['managed_bytes'],
                      info['sha256'])
                return
            except Exception as e:
                failures.append(f'{name}: {e}')
                print('ERROR', failures[-1])
        raise SystemExit('No sound assembly found. ' + '; '.join(failures))

if __name__ == '__main__':
    main()
