# DENDICH / RADIO SILENCE — 3D VTuber

Оригинальная 3D-модель создана с нуля по приложенному производственному ТЗ и трём референсным листам. Геометрия предыдущих моделей репозитория не использована.

## Файлы

- `output/DENDICH_RADIO_SILENCE.vrm` — VRM 1.0.
- `output/DENDICH_RADIO_SILENCE.blend` — редактируемый Blender-исходник.
- `tools/build_dendich.py` — воспроизводимая процедурная сборка.
- `renders/` — настоящие рендеры геометрии из Blender, включая крупный план и выражения.
- `references/` — предоставленные пользователем референсы.

## Возможности

- Полный гуманоидный скелет: корпус, голова, глаза, челюсть, руки, ноги и пальцы.
- VRM 1.0 expressions: Blink/Blink L/R, A/I/U/E/O, Happy, Sad, Angry, Relaxed, Surprised и четыре направления взгляда.
- Дополнительные выражения: Tired, Serious, Irritated, Awkward и What the hell.
- Десять двухзвенных spring-bone цепочек волос с коллайдером головы.
- Отдельные гарнитура, boom-микрофон, PTT, провод, радио, индикатор, подсумки и редактируемые патчи `DENDICH`, `RADIO SILENCE`, `RS-01`.

## Импорт и утренний стрим

Используйте приложение с поддержкой VRM 1.0. VSeeFace официально ориентирован на VRM 0.x, поэтому для этого файла подходят Warudo, VNyan или другое приложение, явно поддерживающее VRM 1.0. После импорта назначьте камеру и микрофон, выполните нейтральную калибровку, затем проверьте моргание и A/I/U/E/O.

Модель и экспорт проверены структурно в Linux. Живой трекинг с физической камерой и поведение пружин в конкретном Windows-приложении требуют финальной проверки на вашем стриминговом ПК.

## Сборка и проверка

```sh
blender -b --factory-startup --python-exit-code 1 --python dendich/tools/build_dendich.py
python dendich/tools/validate_dendich.py
blender -b --factory-startup --python-exit-code 1 --python dendich/tools/render_expressions.py
blender -b --factory-startup --python-exit-code 1 --python dendich/tools/render_exported.py
```

Требуется Blender 4.3+. Скрипт не загружает внешние ассеты и не использует генерацию изображений.
