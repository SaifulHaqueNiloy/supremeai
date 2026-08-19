---
name: frontend-taste
description: Strict guidelines and heuristics to ensure AI-generated UIs have premium "taste", strong typography, layout, motion, and spacing.
---

# SupremeAI Frontend Taste Guidelines

AI agents often generate "slop" interfaces using default frameworks, repetitive card layouts, and basic colors. When acting as a Frontend Engineer for SupremeAI, you must abide by these strict "Taste" rules derived from `impeccable` and `taste-skill`.

## Core Philosophy

1. **Brand Exclusivity**: SupremeAI UIs must feel premium, bespoke, and extremely modern (Glassmorphism, dark modes, subtle glows).
2. **Dynamic & Alive**: Everything should have subtle motion. Micro-animations are mandatory.

## Anti-Patterns (What NOT to do)

- ❌ **DO NOT use Arial, Helvetica, or system defaults.**
- ❌ **DO NOT use Inter for everything.** Use character-rich fonts like `Outfit`, `Manrope`, `Clash Display`, or `Plus Jakarta Sans`.
- ❌ **DO NOT use pure black (`#000000`) or pure gray.** Always tint your grays with the primary brand color (e.g., a dark slate blue).
- ❌ **DO NOT wrap everything in cards.** Use whitespace, dividers, and typography to create hierarchy instead of repetitive boxes.
- ❌ **DO NOT nest cards inside cards.** This looks amateurish.
- ❌ **DO NOT use bounce/elastic easing.** It feels dated.
- ❌ **DO NOT use generic primary colors (plain red/blue/green).** Use HSL values, smooth gradients, and tailored palettes.

## Positive Guidelines (What TO do)

- ✅ **Typography Hierarchy**: Ensure strong contrast in font weights and sizes. A large, bold H1 paired with a subtle, readable body text.
- ✅ **Motion**: Use smooth, custom easing curves for transitions (e.g., `cubic-bezier(0.16, 1, 0.3, 1)`).
- ✅ **Shadows**: Use layered, soft, semi-transparent shadows instead of harsh, single-layer box-shadows. E.g., `box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05), 0 0 3px rgba(0,0,0,0.02)`.
- ✅ **Whitespace**: Be generous with padding and margins. Let the elements breathe.
- ✅ **Subtle Borders**: For dark mode, use extremely subtle borders (e.g., `border: 1px solid rgba(255,255,255,0.05)`) rather than solid gray.

When generating HTML, CSS, React, or Next.js code, apply these principles strictly. Failure to produce a "premium" UI is unacceptable.
