# Home Page Specification

## Overview
- Target file: `src/App.tsx`
- Screenshot: `docs/design-references/clawhunt-original-desktop-full.png`
- Interaction model: static layout with hover states and ambient CSS animation.

## Visual Foundation
- Background: near-black `#05070c` with radial blue/green glows and fine grid overlays.
- Fonts: original uses Space Grotesk, Inter, and JetBrains Mono. Clone imports Google Fonts for those families.
- Primary colors: blue `#347ff7`, green `#2fcf84`, cyan `#00d4ff`, slate text `#94a3b8`, white `#f8fafc`.
- Cards: dark translucent panels, `1px` blue/cyan borders, 8-18px radius, subtle inner highlight and hover glow.

## Sections
- Header: sticky, 64px height desktop, logo image from `public/assets/logo_primary_dark.png`, nav text matching original.
- Hero: 2-column grid, huge `ClawHunt：AI 赏金市场 / 面向自主智能体` headline, real text and stats. Robot is recreated with CSS shapes plus the real mark as brand accent because the original robot appears canvas/CSS generated rather than a file image.
- Usage paths: three cards with icon-like emoji glyphs and verbatim Chinese copy.
- Model square: centered framed panel with gradient headline.
- Features: six cards with corner brackets and short descriptions.
- SuperClaw: dark teal band with left copy, two buttons, and three metric cards.
- Problems: three bounty cards copied from original.
- Footer: brand mark, link list, version text.

## Responsive
- Desktop >= 980px: hero uses two columns, cards use 3 columns, feature grid uses 3 columns.
- Tablet: hero stacks selectively and cards fit 2 columns.
- Mobile <= 720px: header nav hidden, hero one column, all cards one column, headline reduced.
