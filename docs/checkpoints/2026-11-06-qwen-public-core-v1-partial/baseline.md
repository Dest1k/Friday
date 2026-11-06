# PARTIAL — не полный baseline

PARTIAL. Прогон не покрывает все 673 задачи. Неполный знаменатель не выдаётся за полный baseline.

- run: `qwen-public-core-v1-idle-20261028-R1`
- kind: `model`
- state: `PARTIAL` / run `NEEDS_QUIET_WINDOW`
- model field: `qwen38-flash-next-abliterated`
- endpoint alias: <internal-endpoint>
- live_checked: `False`
- full_model_baseline: `False`
- generation fingerprint: `7eda7c6c5b4a9b07a03e371fa6c8d46559358ec0ec96e2642a2950a291f7ea21`
- активное время модели, с: `None`; известная сумма: `327102.956663284`; полнота стоимости: `False`
- незавершённые попытки, известное время, с: `62577.33778947494`; без измерения: `6`; лимит: `отключён (null)`; историческое foreground/stop время: `61400.83865182694`
- CPU scoring и календарное время с паузами в этом отчёте не смешиваются с активным временем. CPU здесь null, пока отдельный таймер скоринга не записан.

Сырые ответы: `requests/`, `predictions/`. Оценки: `reviews/`.

## IFBench

- revision: `2e8a48de45ff3bf41242f927254ca81b59ca3ae2` split `train`
- expected 300, generated 300, scored 300
- attempts 319, truncated 42, transport_errors 0, outcome_unknown 0, technical_losses 1, technical_retries 1, unmeasured_sent_attempts 1
- not_run 0, parse_errors 0, extraction_errors 0, wrong_answers 0, timeouts 0, runtime_errors 0, infrastructure_failures 0
- protocol_complete: `True`
- comparability: `B`
- reference claim 81.3 (https://huggingface.co/Qwen/Qwen3.8-Flash-Next), metric_confirmed=False. Same named benchmark. The card does not publish sample, prompt, shots, generation mode, or attempt count for this score.
- metrics: `{'prompt_level_strict': {'value': 0.7333333333333333, 'numerator': 220, 'denominator_scored': 300, 'denominator_expected': 300}, 'prompt_level_loose': {'value': 0.7366666666666667, 'numerator': 221, 'denominator_scored': 300, 'denominator_expected': 300}, 'inst_level_strict': {'value': 0.747093023255814, 'numerator': 257, 'denominator_scored': 344, 'denominator_expected': None}, 'inst_level_loose': {'value': 0.75, 'numerator': 258, 'denominator_scored': 344, 'denominator_expected': None}}`

## GPQA Diamond

- revision: `master` split `train`
- expected 198, generated 195, scored 195
- attempts 267, truncated 32, transport_errors 0, outcome_unknown 0, technical_losses 3, technical_retries 3, unmeasured_sent_attempts 2
- not_run 3, parse_errors 32, extraction_errors 0, wrong_answers 10, timeouts 0, runtime_errors 0, infrastructure_failures 0
- protocol_complete: `False`
- comparability: `B`
- reference claim 91.7 (https://huggingface.co/Qwen/Qwen3.8-Flash-Next), metric_confirmed=False. Same named benchmark. The card footnotes do not specify the protocol for this score. Our profile is 0-shot generative CoT, one sample.
- metrics: `{'accuracy': {'value': 0.7846153846153846, 'numerator': 153, 'denominator_scored': 195, 'denominator_expected': 198}}`

## LiveCodeBench v6 (config v6, 175)

- revision: `175d0ac20500fd7aa0813f7a2e6ae7ecad3c76c9` split `test`
- expected 175, generated 173, scored 173
- attempts 235, truncated 75, transport_errors 0, outcome_unknown 0, technical_losses 3, technical_retries 3, unmeasured_sent_attempts 3
- not_run 2, parse_errors 0, extraction_errors 75, wrong_answers 4, timeouts 0, runtime_errors 0, infrastructure_failures 0
- protocol_complete: `False`
- comparability: `C`
- reference claim 91.9 (https://huggingface.co/Qwen/Qwen3.8-Flash-Next), metric_confirmed=False. The card label v6 is ambiguous with release_v6=1055. This profile pins config v6 = 175 problems at revision 175d0ac, contest dates 2025-01-04 through 2025-04-06. Author subset is not confirmed.
- metrics: `{'all_tests_pass': {'value': 0.5433526011560693, 'numerator': 94, 'denominator_scored': 173, 'denominator_expected': 175}}`

Null значит «не измерялось», не ноль.
Неверный ответ, ошибка извлечения, инфраструктурный сбой и не запущенная задача — разные поля.
