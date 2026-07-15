# Design system

The look is a dark, calm, high-contrast slide aesthetic. Tokens and layout primitives live in `src/tokens.css` and `src/slides.css` (the engine — don't edit them per-deck; override in a slide's scoped `<style>` or reskin the palette as below).

## Tokens

| Token | Value | Use |
|-------|-------|-----|
| `--bg` | `#0b1120` | page background |
| `--panel` / `--panel-2` | `#1e293b` / translucent | card backgrounds |
| `--text` / `--text-dim` / `--text-faint` | slate 200 / 400 / 500 | body / secondary / captions |
| `--blue`,`--green`,`--purple`,`--amber`,`--red`,`--cyan` | accents | category colors |
| `--<accent>-lt` | light variant | the accent as **text on dark** (use the `-lt` for type) |
| `--line` | translucent slate | borders, rules, axes |
| `--radius` | `12px` | card corners |
| `--step-ms` | `360ms` | reveal transition duration |

Rule of thumb: fills and borders use the base accent; text uses the `-lt` variant so it stays legible on `--bg`.

## Reskinning the palette

Change the six accent pairs and the neutrals in `src/tokens.css` — everything references the vars, so a reskin is a dozen edits and no markup changes. Keep every accent's `-lt` genuinely lighter (it's load-bearing for text contrast). For a light-background deck you'd invert `--bg`/`--text` and darken the `-lt` variants; test contrast on the criteria table and chart, which lean on accents hardest. The default palette is a sibling of the OWASP threat-surface aesthetic.

## Typography and the frame

- The deck renders in a **16:9 frame** sized `min(100vw, 100vh·16/9)`, letterboxed, designed at 1920×1080.
- Type uses `clamp(min, N·vw, max)`. `vw` is the **viewport** width, not the frame's. The `min` protects tiny windows; the `max` caps huge ones; the `vw` term governs in between.
- Headings: `clamp(30px, 4.4vw, 64px)`. Body: `clamp(18px, 2vw, 30px)`. Match these tiers so slides feel consistent.

## The step-reveal primitive

Anything with `data-step` starts hidden (`opacity:0; translateY(10px)`) and animates in when it gets `.on` (current step ≥ its number). You get staged reveals for free — **no keyframes needed**. Reserve `@keyframes` for a single, deliberately animated slide and list it in `manifest.animatedSlides`. `prefers-reduced-motion` already disables transitions and animations.

## Layout rules

- Slides are `display:flex; flex-direction:column` with `4.5% 6%` padding. Lay out with flex/grid and `min-height:0` on scrollable children so content fits without a scrollbar.
- **Scope every rule** to `[data-slide="<id>"]`. Unscoped selectors leak across slides.
- Budget vertical space with **flex ratios**, not fixed heights — the frame's height varies with the viewport.

## The 960px viewport — where decks actually break

Presenters often run the audience window on a laptop at roughly **960px CSS-px wide**. Every layout bug that shipped in testing showed up there, not at full-screen. The recurring failure modes and their fixes:

1. **Percentage vertical padding scales with *width*, not height.** A slide that fits at 1080p overflows its frame at 960px because `padding: 3%` and `margin: 3%` shrink horizontally but the content's height doesn't. Fix: budget vertical space with flex (`flex: N 1 0%`, `min-height:0`), not percentage padding, on dense slides.
2. **`clamp()` max caps don't compress.** A `clamp(…, …, 30px)` cap stays 30px on a small screen, so a slide with many rows overflows. Fix: when a slide overflows, **lower the whole size tier** (drop every clamp cap on that slide one notch) rather than nudging one element — the elements are sized relative to each other and must move together.
3. **Absolute-positioned labels drift.** Labels placed with absolute coordinates separate from their target at a different aspect ratio. Fix: position labels relative to their container, and keep a subtext line a fixed offset below its heading (not an independent absolute coordinate).
4. **SVG scales uniformly and safely** — author at a fixed `viewBox` and it shrinks cleanly. But SVG `<text>` does **not** reflow; keep every label inside its box at the design size, and relocate anchors rather than trusting them to wrap.
5. **Cards clip their content.** `overflow:hidden` on a card plus text sized by `vw` clips at narrow widths. Fix: scope the text sizes down inside the card, or drop `overflow:hidden` once you've confirmed it won't collide.

**Always** open the built `slides.html` in a real browser at the presenter's actual window size and step through every slide. `qa.py` verifies structure, not pixels — it will pass on a slide that overflows. Use `python3 build.py --preview <id>` to iterate on one slide in isolation.
