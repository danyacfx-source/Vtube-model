from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
root=Path(__file__).resolve().parents[1];out=root/'DENDICH_RADIO_SILENCE_VRM1.zip'
files=[root/'README.md',root/'validation.md']+[p for folder in ['output','renders','tools','references'] for p in sorted((root/folder).iterdir()) if p.is_file() and '__pycache__' not in str(p)]
with ZipFile(out,'w',ZIP_DEFLATED) as z:
    for p in files:z.write(p,p.relative_to(root))
with ZipFile(out) as z:assert z.testzip() is None
print(out.name,out.stat().st_size,'bytes; CRC PASS')
