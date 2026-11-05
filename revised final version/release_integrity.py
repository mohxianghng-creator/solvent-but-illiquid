"""Read-only integrity verification; --seal is an explicit release-author operation.

Hashes detect changes relative to this local baseline, not malicious replacement of
both files and manifest. This is not a digital signature or independent attestation.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parent
EXCLUDED={'sources','work','__pycache__','.git','.venv','.pytest_cache','.ruff_cache'}


def release_files(root):
    return sorted(p for p in root.rglob('*') if p.is_file()
        and not any(part in EXCLUDED for part in p.relative_to(root).parts)
        and p.name!='MANIFEST_SHA256.txt')


def verify(root=ROOT):
    root=Path(root).resolve()
    entries={}
    for line in (root/'MANIFEST_SHA256.txt').read_text(encoding='utf-8-sig').splitlines():
        digest,relative=line.split('  ',1)
        path=PurePosixPath(relative)
        if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Invalid manifest digest')
        if path.is_absolute() or '..' in path.parts or '\\' in relative or ':' in relative or relative in entries:
            raise ValueError('Unsafe or duplicate manifest entry')
        entries[relative]=digest
    if not entries:
        raise ValueError('Empty release manifest')
    actual={p.relative_to(root).as_posix():p for p in release_files(root)}
    missing=set(entries)-set(actual); extra=set(actual)-set(entries)
    if missing or extra:
        raise ValueError(f'Release inventory differs: missing={sorted(missing)}, added={sorted(extra)}')
    changed=[name for name,digest in entries.items()
        if hashlib.sha256(actual[name].read_bytes()).hexdigest()!=digest]
    if changed:
        raise ValueError('Release content changed: '+', '.join(changed))
    return len(entries)


def seal(root=ROOT):
    root=Path(root).resolve()
    rows=[hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(root).as_posix()
        for p in release_files(root)]
    (root/'MANIFEST_SHA256.txt').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    return len(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal',action='store_true',help='Explicitly replace local integrity baseline after reviewing a new release')
    args=parser.parse_args()
    print(f'{seal() if args.seal else verify()} release files '+('sealed' if args.seal else 'verified (read-only)'))


if __name__=='__main__': main()
