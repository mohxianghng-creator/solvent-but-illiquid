"""Re-extract material company facts from primary PDF; fail on changed values or layout.

Offline by default. --online independently downloads the same historical report and
records retrieval time and hashes without replacing the frozen source snapshot.
No private daily claims or executable investment data are inferred here.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from html.parser import HTMLParser
import numpy as np
import pandas as pd
import pymupdf

ROOT = Path(__file__).resolve().parent
NUMBER = r'\(?-?\d[\d,]*(?:\.\d+)?\)?'


def number(value):
    return float(value.replace(',', '').replace('(', '-').replace(')', ''))


def pair(text, label, note='', count=2):
    pattern = re.escape(label) + r'\s+'
    if note:
        pattern += re.escape(note) + r'\s+'
    pattern += r'\s+'.join('(' + NUMBER + ')' for _ in range(count))
    matches = list(re.finditer(pattern, text, flags=re.I))
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one source row: {label}; got {len(matches)}')
    return [number(v) for v in matches[0].groups()]


def extract_company(path):
    """PDF pages are one-based; amounts converted from NZD000 to NZDm."""
    with pymupdf.open(path) as doc:
        pages = {p: doc[p-1].get_text() for p in [45, 47, 64, 70, 82]}
    records = []
    def add(field, values, page, unit='NZDm'):
        for year, value in zip([2025, 2024], values):
            records.append(dict(year=year, field=field, value=value, unit=unit, pdf_page=page))
    for field, label, note in [('cash', 'Cash and cash equivalents', '8.1'), ('investments', 'Investments', '3.2')]:
        add(field, np.array(pair(pages[45], label, note))/1000, 45)
    for field, label, note in [
        ('premiums_received','Premiums received for insurance contracts issued',''),
        ('claims_and_service_paid','Insurance claims paid and other insurance service expenses',''),
        ('recoveries_received','Reinsurance recoveries received',''),
        ('operating_net','Net cash inflow from operating activities','8.1'),
        ('investing_net','Net cash outflow from investing activities',''),
        ('financing_net','Net cash outflow from financing activities',''),
        ('fx','Effect of foreign exchange rate changes',''),
        ('opening_cash','Cash and cash equivalents at the beginning of the year','')]:
        values = np.array(pair(pages[47], label, note))/1000
        if field == 'claims_and_service_paid':
            values = -values  # CSV uses positive paid-cash magnitudes.
        add(field, values, 47)
    for field, label in [('interest_income','Interest income'),('total_investment_income','Investment income')]:
        add(field, np.array(pair(pages[64], label))/1000, 64)
    fixed = re.findall(r'Fixed interest investments\s+\S+\s+([\d,]+)\s+\S+\s+([\d,]+)', pages[64])
    if len(fixed) != 2 or any(x != y for x, y in fixed):
        raise ValueError('Unexpected fixed-interest hierarchy table')
    add('fixed_interest', [number(row[0])/1000 for row in fixed], 64)
    for field, label in [('lic_3m','Within 3 months'),('lic_3to6m','3 to 6 months'),('lic_6to12m','6 to 12 months'),('lic','Total')]:
        add(field, np.array(pair(pages[70], label, count=4)[:2])/1000, 70)
    rate = re.search(r'deposits is ([\d.]+)% \(2024: ([\d.]+)%\)', pages[82])
    png = re.search(r'NZD ([\d.]+)m \(2024: NZD ([\d.]+)m\) held in Papua New Guinea', pages[82])
    solomon = re.search(r'NZD ([\d.]+)m \(2024: NZD ([\d.]+)m\) held in the\s+Solomon Islands', pages[82])
    if not all([rate, png, solomon]):
        raise ValueError('Deposit-rate or restricted-cash source text changed')
    add('deposit_rate', [float(v)/100 for v in rate.groups()], 82, 'fraction')
    add('restricted_png', [float(v) for v in png.groups()], 82)
    add('restricted_solomon', [float(v) for v in solomon.groups()], 82)
    return pd.DataFrame(records)


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.row=None; self.cell=None
    def handle_starttag(self, tag, attrs):
        if tag == 'tr': self.row=[]
        if tag in ('td','th') and self.row is not None: self.cell=[]
    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data)
    def handle_endtag(self, tag):
        if tag in ('td','th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split())); self.cell=None
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row); self.row=None


def extract_kaikoura(path):
    parser=TableParser(); parser.feed(path.read_text(encoding='utf-8'))
    totals=[r for r in parser.rows if r and r[0].strip().upper()=='TOTAL']
    if len(totals)!=1 or len(totals[0])!=5:
        raise ValueError('Unexpected Kaikoura received/settled table')
    row=totals[0]
    return dict(reported_cost=number(row[2]), paid_lower=number(row[4]))


def audit(root=ROOT):
    manifest=pd.read_csv(root/'data/source_retrieval_manifest.csv')
    if not (manifest.status=='retrieved').all() or manifest.file.duplicated().any():
        raise ValueError('Incomplete or ambiguous source manifest')
    for row in manifest.itertuples():
        path=(root/'sources'/row.file).resolve()
        if not path.is_relative_to((root/'sources').resolve()):
            raise ValueError('Source file escapes source directory')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=row.sha256 or path.stat().st_size!=row.bytes:
            raise ValueError(f'Source integrity failure: {row.file}')
    extracted=extract_company(root/'sources/Tower_2025_Official.pdf')
    published=pd.read_csv(root/'data/tower_financial_evidence.csv').set_index('year')
    for r in extracted.itertuples():
        if not np.isclose(published.loc[r.year,r.field],r.value,atol=1e-9,rtol=0):
            raise ValueError(f'Source mismatch: {r.year} {r.field}')
    evidence=pd.read_csv(root/'data/payment_evidence.csv')
    required=['paid_lower','reference','weeks','lower_fraction']
    if not np.isfinite(evidence[required].to_numpy()).all():
        raise ValueError('Missing or nonfinite payment evidence')
    if (evidence.paid_lower<0).any() or (evidence.reference<=0).any() or (evidence.weeks<0).any():
        raise ValueError('Invalid payment evidence domain')
    if ((evidence.paid_upper<evidence.paid_lower)&evidence.paid_upper.notna()).any():
        raise ValueError('Reversed payment bounds')
    if not np.allclose(evidence.lower_fraction,evidence.paid_lower/evidence.reference,rtol=0,atol=1e-12):
        raise ValueError('Incorrect lower payment fractions')
    finite=evidence.paid_upper.notna()
    if not np.allclose(evidence.loc[finite,'upper_fraction'],evidence.loc[finite,'paid_upper']/evidence.loc[finite,'reference'],rtol=0,atol=1e-12):
        raise ValueError('Incorrect upper payment fractions')
    if not evidence.loc[~finite,'upper_fraction'].isna().all():
        raise ValueError('Censored payments must retain an open upper bound')
    expected_weeks=(pd.to_datetime(evidence.date)-pd.to_datetime(evidence.start)).dt.days/7
    if not np.allclose(evidence.weeks,expected_weeks):
        raise ValueError('Incorrect event clocks')
    if not set(evidence.source).issubset(set(manifest.url)):
        raise ValueError('Payment evidence lacks a cached primary source')
    url='https://www.icnz.org.nz/industry/media-releases/private-insurers-paid-out-0-5-billion-kaikoura-earthquake-claims/'
    file=manifest.loc[manifest.url==url,'file'].item()
    actual=extract_kaikoura(root/'sources'/file)
    row=evidence[(evidence.event=='kaikoura')&(evidence.date=='2017-06-30')].iloc[0]
    for field,value in actual.items():
        if row[field]!=value: raise ValueError(f'Kaikoura source mismatch: {field}')
    extracted['source_sha256']=hashlib.sha256((root/'sources/Tower_2025_Official.pdf').read_bytes()).hexdigest()
    return extracted, dict(company_source_assertions=len(extracted),kaikoura_source_assertions=len(actual),
        payment_rows_structurally_validated=len(evidence),cached_sources_hashed=len(manifest),
        scope='Company fields and one exact event table machine-extracted. Remaining event transcriptions require manual semantic review; hashes do not prove correctness.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--online',action='store_true',help='Verify historical issuer report against live download, without replacing cached evidence')
    parser.add_argument('--check',action='store_true',help='Read-only local audit; do not regenerate evidence outputs')
    args=parser.parse_args()
    if args.check and args.online: parser.error('--check and --online are mutually exclusive')
    extracted,summary=audit()
    if args.online:
        import requests
        manifest=pd.read_csv(ROOT/'data/source_retrieval_manifest.csv')
        source=manifest[manifest.file=='Tower_2025_Official.pdf'].iloc[0]
        response=requests.get(source.url,timeout=(15,120))
        response.raise_for_status()
        digest=hashlib.sha256(response.content).hexdigest()
        receipt=dict(url=source.url,retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
            bytes=len(response.content),sha256=digest,matches_frozen_source=digest==source.sha256)
        (ROOT/'results/live_source_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
        if not receipt['matches_frozen_source']:
            raise ValueError('Live report differs: investigate revision; cached evidence was preserved')
        summary['live_report_matches']=True
    if not args.check:
        extracted.to_csv(ROOT/'results/primary_source_assertions.csv',index=False)
        (ROOT/'results/data_audit.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
