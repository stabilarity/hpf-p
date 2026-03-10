# HPF-P Utilities

Developer utilities for the HPF-P (Holistic Portfolio Framework for Pharma) project.

## fix_mermaid_wp.py

Fixes Mermaid diagram encoding when publishing to WordPress.

WordPress's `wpautop` filter corrupts Mermaid diagram syntax by inserting `<br>` tags and escaping special characters. This script post-processes HTML content before or after WordPress import to restore correct Mermaid syntax.

### Usage

```bash
python fix_mermaid_wp.py input.html output.html
```

### Part of HPF-P

- Research hub: https://hub.stabilarity.com/hpf-p-framework/
- Framework: DRI (Decision Readiness Index) + DRL (Decision Readiness Level)
- Application: AI Portfolio Optimisation for pharma SKU portfolios
