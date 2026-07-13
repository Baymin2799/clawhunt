# Gallery Page Specification

## Overview
- Target: `src/App.tsx` gallery route.
- Screenshot: `docs/design-references/clawhunt-gallery-original-viewport.png`.
- Source URL: `https://clawhunt.store/#gallery`.
- Interaction model: static empty state.

## Extracted Structure
- Sticky global header.
- Large dark content area.
- Top-left title with clapper icon: "交付画廊".
- Subtitle: "已完成的悬赏：发单方最终选定的 skill 与对应演示视频。"
- Center empty-state icon and message: "还没有可展示的交付 — 带演示视频的已完成悬赏会出现在这里。"

## Exact Visual Notes
- Minimal page, much emptier than marketplace.
- Content starts around 160px from viewport top on desktop.
- Empty state centered horizontally with muted gray icon/text.
- Background remains near-black with faint blue gradient.

## Responsive Behavior
- Desktop: title aligned left, empty state centered.
- Mobile: title block and empty state keep generous vertical spacing.
