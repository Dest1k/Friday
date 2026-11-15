# Calc LOAD: системный размер бумаги — SOURCE и отдельный fixture

Stock PaperInfo при пустом ooSetupSystemLocale вызывает
`popen("paperconf 2>/dev/null", "r")` до LC_PAPER fallback. LC_ALL/LC_PAPER не
устраняют этот вызов. Обход без spawn с сохранением того же reference не доказан.
Ни локаль, ни default paper, профиль или binary здесь не изменяются.

Предложенный узкий контракт — DESIGN, не реализованный observer и не live-допуск.
Он учитывает один popen и два дочерних PID; generic IDLE не заменяет LOAD-marker.
Нужны exact caller/callsite/command/mode/image/argv/FD/deadline guards, оба terminal
exit, сохранённая Office identity и запрет helper во время METRIC. Исходные
native64/raw32/10digits/font/CAS/close/cgroup guards сохраняются.

```mermaid
flowchart LR
  O["Office или tiny parent"] -->|"vfork / posix_spawn"| S["dash"]
  S -->|vfork| P["paperconf"]
  P -->|"exit 3"| S
  S -->|"exit 3 / pclose 768"| O
```

Независимый настоящий nonOffice fixture в той же masked namespace наблюдал
именно эту топологию: два vfork и два exec, stdout0B, paperconf3/dash3/pclose768.
C-fixture намеренно вернул91, отметив неуспех helper; GDB0 означает завершённое
наблюдение. Это не успешная работа paperconf и не выполнение Office fallback.
Все6hostPIDs отсутствуют; binary/scratch удалены, lock освобождён.

follow-parent/detach-off/schedule-multiple ON дошли до всех3 terminal exit;
на exec GDB выбрал inferior2/3, после exit нужен явный выбор живого original1.
Режим OFF не испытывался, поэтому необходимость ON относительно OFF не доказана.
Actual libc2.43: первоначальный source2.42 не использован как version proof;
exact Ubuntu2.43 source проверен отдельно. Exec-stop показывает loader до загрузки
последующих библиотек: будущие libc/libpaper maps не являются pre-PASS.

Архив содержит точные source proposal и исполнявшийся tiny fixture; пути тестовой
среды сохранены. Он не является будущим enforcing guard. Такой coherent SOURCE
кандидат готовится отдельно; Root проверит его политику на реальном fixture до
возможной новой private Office операции. Original R2/R3 LOAD/effects/clocks не
повторяются для зелёного статуса. Installed224 unchanged; M, historical
applicability, physical/user/App/formal F04/B00/V3 acceptance OPEN.

Private документы/профили/байты кэша/plans/grants/rawlogs не публикуются.
