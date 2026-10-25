# Проверка DENDICH / RADIO SILENCE

- Blender 4.3.2: исходник создан с нуля скриптом `build_dendich.py`, сохранён как `.blend`, отрендерены фронтальный, 3/4 и крупный планы.
- Структурная проверка VRM: VRM 1.0, 25 humanoid bones, 17 стандартных presets, 5 custom expressions, 10 spring-bone цепочек волос, 98 971 треугольник.
- Пресеты: Blink/BlinkLeft/BlinkRight, A/I/U/E/O, Happy, Sad, Angry, Relaxed, Surprised, LookLeft/Right/Up/Down.
- Дополнительные выражения: Tired, Serious, Irritated, Awkward, What the hell. Все состояния отрендерены из shape keys в Blender.
- Khronos glTF Validator: 0 ошибок. Предупреждения: 97 `NODE_SKINNED_MESH_NON_ROOT` из-за отдельных skinned деталей под общей арматурой; 77 информационных сообщений о служебных accessor; два сообщения о неподдерживаемых валидатором VRM-расширениях. Это не ошибки геометрии или контейнера.
- Выполнен повторный импорт конечного `.vrm` как glTF и отдельный рендер `DENDICH_exported_roundtrip.png`.
- Физическая камера, трекинг и динамика spring bones в Windows-приложении в этой Linux-среде не проверялись.
