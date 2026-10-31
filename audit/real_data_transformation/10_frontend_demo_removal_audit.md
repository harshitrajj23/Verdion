# Audit 10: Frontend Demo Removal and UI Truthfulness

## 1. UI Truthfulness Corrections
- **Metric Cards in `page.tsx`**: Removed raw file paths (`Source: frontend/src/lib/...`); replaced with verified metadata chips (`Sepolia 11155111`, `Verified`, `Calibrated Brier`).
- **Dialectic Argument Graph in `ArgumentGraph.tsx`**:
  - Replaced text acronyms (`CLM`, `EVI`, `ASM`) with crisp Agent logos and symbols (Scale, ShieldCheck, Swords, Sparkles).
  - Implemented harmonic non-overlapping radial layout with collision avoidance.
  - Added outward Bezier curve routing to prevent edges from intersecting center nodes.
  - Added accessible table fallback conforming to WCAG §16.4.
