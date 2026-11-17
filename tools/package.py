"""Create a deterministic source/data zip from an explicit allowlist."""
import argparse,hashlib,zipfile
from pathlib import Path
from common import ROOT
from validate import validate

def package(output):
    validate();output=Path(output).resolve()
    allowed_dirs={'data','sources','schema','docs','tools','tests','examples','.github'}
    allowed_files={'README.md','LICENSE','DATA_RIGHTS.md','.gitignore','.gitattributes','pyproject.toml','taxonomy.json'}
    paths=[]
    for p in ROOT.rglob('*'):
        rel=p.relative_to(ROOT)
        if not p.is_file() or any(s in {'__pycache__','.git','runs','.venv'} for s in rel.parts):continue
        if len(rel.parts)==1 and rel.name not in allowed_files:continue
        if len(rel.parts)>1 and rel.parts[0] not in allowed_dirs:continue
        if p.suffix in {'.pyc','.pdf','.png','.html','.zip'}:continue
        paths.append(p)
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(paths):
            info=zipfile.ZipInfo('Probability-Bench/'+p.relative_to(ROOT).as_posix(),date_time=(2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,p.read_bytes())
    print(f'{output}\nSHA256 {hashlib.sha256(output.read_bytes()).hexdigest()}\n{len(paths)} files')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);package(p.parse_args().output)
