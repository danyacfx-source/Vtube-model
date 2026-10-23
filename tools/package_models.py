"""Package the current models and sources; verify ZIP CRCs before publication."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root=Path(__file__).resolve().parents[1]
for name,paths in [
    ('VSeeFace-fruits.zip',[root/'models/orange.vrm',root/'models/pineapple.vrm',root/'README.md']),
    ('Fruit-avatars.zip',[root/'README.md']+[p for folder in ['models','previews','tools','validation'] for p in sorted((root/folder).iterdir()) if p.is_file()]),
]:
    with ZipFile(root/name,'w',ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path,path.name if name=='VSeeFace-fruits.zip' else path.relative_to(root))
    with ZipFile(root/name) as archive:
        assert archive.testzip() is None
    print(name, 'CRC checks passed')
