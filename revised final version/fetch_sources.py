"""Obtain exact historical source snapshots locally; never silently accept changed pages."""
import argparse, csv, hashlib, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--download',action='store_true')
    group.add_argument('--from-directory',type=Path,help='An authorised copy of the original sources directory')
    args=ap.parse_args()
    rows=list(csv.DictReader((ROOT/'data/source_retrieval_manifest.csv').open(encoding='utf-8-sig',newline='')))
    staged=[]
    for row in rows:
        name=row['file']
        if Path(name).name!=name or '/' in name or '\\' in name:
            raise ValueError('Unsafe source filename')
        target=ROOT/'sources'/name
        if target.is_file(): body=target.read_bytes()
        elif args.from_directory: body=(args.from_directory/name).read_bytes()
        else:
            request=urllib.request.Request(row['url'],headers={'User-Agent':'Mozilla/5.0 historical research verification'})
            with urllib.request.urlopen(request,timeout=120) as response: body=response.read()
        if len(body)!=int(row['bytes']) or hashlib.sha256(body).hexdigest()!=row['sha256']:
            raise ValueError(f'{name}: live/local bytes differ from historical snapshot. Obtain the exact snapshot; do not update the baseline to pass.')
        staged.append((target,body))
    for target,body in staged:
        target.parent.mkdir(exist_ok=True)
        if not target.exists():target.write_bytes(body)
    print(f'{len(staged)} historical sources available locally and hash-verified; sources/ is excluded from Git.')

if __name__=='__main__':main()
