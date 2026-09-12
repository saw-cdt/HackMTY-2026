.PHONY: check-format check-isolation

# La estructura de salida (findings, leads_not_pursued, run_metadata) es
# correcta segun el validador oficial de los organizadores.
check-format:
	python3 validate_format.py --submission out/submission.json

# ground_truth no puede aparecer fuera de src/generate/ (ni siquiera
# importado): si el agente lo puede leer, la metrica no vale nada.
check-isolation:
	@files=$$(grep -rl 'ground_truth' src/ --include='*.py' 2>/dev/null || true); \
	offenders=""; \
	for f in $$files; do \
		case "$$f" in \
			src/generate/*) ;; \
			*) offenders="$$offenders $$f" ;; \
		esac; \
	done; \
	if [ -n "$$offenders" ]; then \
		echo "FAIL: 'ground_truth' aparece fuera de src/generate/ en:$$offenders"; \
		exit 1; \
	else \
		echo "OK: 'ground_truth' no aparece fuera de src/generate/"; \
	fi
