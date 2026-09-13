# FEAT-005-VERIFY — Verification Pass: Latency Benchmarks & Adversarial Evaluation (P1)

**Files being verified**: `FEAT-005-INT-eval-and-benchmarks.md`

---

## 1. Test Suite Execution
Run the automated benchmark and adversarial evaluation suites:
```bash
python -m tests.benchmark_latency
python -m tests.eval_adversarial
```

### Required Test Case Assertions
- [ ] `test_benchmark_runner_calculates_mean_ttft`: PASS
- [ ] `test_benchmark_runner_measures_tokens_per_sec`: PASS
- [ ] `test_adversarial_evaluator_flags_off_topic`: PASS
- [ ] `test_adversarial_evaluator_flags_leakage`: PASS
- [ ] `test_report_exporter_writes_valid_markdown`: PASS

---

## 2. Acceptance Criteria Individual Re-Check
- [ ] AC-1: Average TTFT and throughput measured over sample prompts: **PASS/FAIL**
- [ ] AC-2: 100% of tested adversarial prompts deflected gracefully: **PASS/FAIL**
- [ ] AC-3: Scripts exit with return code 0 on complete evaluation: **PASS/FAIL**
- [ ] AC-4: Markdown report saved to `feature-test-reports/FEAT-005-test-report.md`: **PASS/FAIL**

---

## 3. Definition of Done Compliance
- [ ] Benchmark data recorded on CPU hardware and validated.
- [ ] Adversarial deflection rate is exactly 100%.
- [ ] SQA test report committed in `feature-test-reports/FEAT-005-test-report.md`.
- [ ] All verification criteria across `INDEX.md` confirmed.

---

## 4. Remediation Rule
If any check fails:
1. Do NOT mark `FEAT-005-INT` complete.
2. If deflection fails, strengthen the system prompt deflection directives in `backend/conversation/orchestrator.py`.
3. If latency is below target, review model quantization and context window size.
4. Re-run until 100% pass rate is achieved.
5. Update `context/feature-specs/INDEX.md` status only after full pass.
