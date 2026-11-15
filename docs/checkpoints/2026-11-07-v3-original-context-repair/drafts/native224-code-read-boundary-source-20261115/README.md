# Граница чтения CODE при подготовке224

Архив проверенной операционной дельты конструктора, использованной Root до
SourceAcceptance224. Это не новый продуктовый слой и не отдельный допуск.
Оригинал и afterimage сохраняются в приватных материалах; patch содержит код.

- Before:25427B, SHA256 `5d33989ccb219617730e8f99206a165b1b05506bcb48af4de603e2fe16661942`.
- After:28766B, SHA256 `d357482556867019c61f1a823ceec44ae329e88c9679cbcf7a1b4e1d736c65e6`.
- Независимо проверенный RESULT: `0ed08a1377e05ba2d9b340df259e2ded961ff81683ef1bb2f040394b9c5590e6`.

Легитимный inherited compressor CODE patch21390899B превышал общий16MiB cap.
Для точного sealed95 CODE inventory установлен32MiB leaf cap. Метаданные,
operator/source refs остаются16MiB; caller не может выбрать увеличенный лимит.
Сохранены происхождение, safe path, owner/single-link, hash, frozen identity,
mode и before/open/after CAS. Три inventory дают1585CODE leaves.

Проверки неизменного afterimage:26controls, весь CODE closure и независимое review.
В ходе первоначальных проверок временно возникли2pyc; собственные файлы/cache
удалены, изменение metadata каталогов сохранено как исторический инцидент.
Это не blanket утверждение о неизменности metadata;23source bytes и sealed95
сохранены. Исторический отказ не переписан. Повторный полный gate не запускался.

[Точный r5 SourceAcceptance и prepare](../../evidence/astra-20261115/source224-r5-accepted-and-current-prepared.json).
Установка и postconditions публикуются отдельно.16/32MiB — пределы чтения
конструктора, не пользовательский file-size контракт Friday.
