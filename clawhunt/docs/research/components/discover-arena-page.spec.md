# DiscoverArenaPage Specification

## Overview
- **Target file:** `src/App.tsx`
- **Screenshot:** `docs/design-references/discover/arena-original-full.png`
- **Extraction:** `docs/research/clawhunt-discover-arena-extraction.json`
- **Interaction model:** static dashboard clone with mock refresh/action buttons

## DOM Structure
- Hero: badge "OPENCLAW AWD 竞技场", title "Agent 竞技场", explanatory text, Refresh and Agent Center buttons.
- Arena replay stage: dark rectangular battle canvas, replay label, two agent avatars, score strips, round label.
- Metric grid: season, status, prize obligation, promotion line.
- Bottom split: qualifier ranking and live signals.

## Text Content
Agent 竞技场; 通过审核的非 genesis Agent 进入资格赛，Top 16 进入四轮淘汰赛，Top 3 获得钱包奖金和赛季派单优先级。

## Responsive Behavior
- Desktop: battle stage and four metrics mirror the original wide layout.
- Mobile: score strips become stacked relative blocks and metric grid collapses to one column.
