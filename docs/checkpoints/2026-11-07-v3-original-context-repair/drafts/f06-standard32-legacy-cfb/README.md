# F06: Standard3.2 — проверенный исходный кандидат

Пять существующих native-файлов добавляют ограниченное чтение и сохранение
шифрования Standard3.2 AES128/ECB/SHA1 с заданным паролем. Разрешён только
проверенный профиль CFB; строгий Agile4.4 и его HMAC сохраняются. Standard
возвращает password_verified=true, data_integrity_verified=false: проверка
пароля и ZIP не является аутентификацией содержимого.

Патч и pins — точные байты завершённого Task21. Это исходники от203, а не
установленный слой. Полный friday_prompt_scope.py из203 нельзя подставлять
в205: только два guidance-hunk поверх настоящего205 с сохранением F04.
Сол Task22 готовит совместный пакет205 + privacy + modernODT taxonomy.

Независимые primitive/consumer/composition/password-boundary проверки приняты
в своих границах; Root проверил41 ссылку/условие без повторного исполнения.
Девять новых source-наблюдений на тех же трёх сохранённых ciphertext показали
missing/wrong/correct password поведение. Raw SOURCE_CHECKS_FAILED сохранён:
проверяющий ошибочно требовал общий ALPHA17, не соответствующий исходным
семантическим критериям. Исправленная трактовка не даёт full semantic PASS.
Производитель, NativeR3, настоящие правки этих трёх файлов, Office и отправки
не повторялись. Genuine edited derivatives этим заданием не создавались.

Код не установлен, ordinary F06/B00/полный170/120 не принят. Подробные pins,
review, ошибки, границы и private evidence связаны в public evidence JSON.
