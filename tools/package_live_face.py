"""Build the standalone offline-camera archive."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
root=Path(__file__).resolve().parents[1]
with ZipFile(root/'Live-fruits-camera.zip','w',ZIP_DEFLATED) as archive:
    for path in sorted((root/'live-face').rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            archive.write(path,path.relative_to(root/'live-face'))
with ZipFile(root/'Live-fruits-camera.zip') as archive:
    assert archive.testzip() is None
    names=set(archive.namelist())
    assert {'Запустить.bat','serve.py','index.html','app.js','models/orange.vrm','models/pineapple.vrm','vendor/mediapipe/face_mesh.js'}<=names
print('Live-fruits-camera.zip: contents and CRC checks passed')
