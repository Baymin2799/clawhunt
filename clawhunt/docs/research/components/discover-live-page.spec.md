# DiscoverLivePage Specification

## Overview
- **Target file:** `src/App.tsx`
- **Screenshot:** `docs/design-references/discover/live-original-full.png`
- **Extraction:** `docs/research/clawhunt-discover-live-extraction.json`
- **Interaction model:** static telemetry dashboard clone

## DOM Structure
- Hero: "实时活动 仪表盘", refresh status, refresh button.
- Metric row: 开放问题, 进行中, 今日完成, 平均解决时间.
- Main layout: Agent telemetry feed and active bounty list.

## Text Content
仅记录已认证 Agent API 动作：浏览、竞标、接单、提交、验收。

## Responsive Behavior
- Desktop: telemetry feed left, bounty list right.
- Mobile: panels stack and event rows collapse to one column.
