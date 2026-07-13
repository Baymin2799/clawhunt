# Marketplace Page Specification

## Overview
- Target: `src/App.tsx` marketplace route.
- Screenshot: `docs/design-references/clawhunt-marketplace-original-full.png`.
- Source URL: `https://clawhunt.store/marketplace`.
- Interaction model: static filters and hoverable cards for this clone.

## Extracted Structure
- Sticky global header.
- Page container `page-marketplace`, dark background, top spacing, max-width content.
- Header row: "问题任务市场", "浏览 赏金任务", "+ 发布新问题", result count.
- Compact filter rows: difficulty, category, status, type, time, bounty, sort.
- Discovery panel: "发现 / 热门解决方案 / 刷新 ->" plus horizontal solution cards.
- Main bounty grid: desktop three columns, dense dark cards with tags, status, title, description, bids/date, reward.

## Exact Visual Notes
- Background: near-black `#05070c` with subtle blue/green radial glow.
- Cards: `rgba(8, 13, 23, 0.72)` to `rgba(12, 20, 38, 0.94)`, 1px cyan/blue border, 8-12px radius.
- Text hierarchy: white titles, slate secondary text, cyan/green/orange status values.
- Layout: content starts below 64px header, compact and dashboard-like, not a marketing hero.

## Text Content
- Problem market header and filters from extraction: 全部, 简单, 中等, 困难, 专家, Python, JavaScript, ML/AI, 数据, API, 运维.
- Hot solution cards: theme toggle, CI/CD pipeline, E2E suite, REST API rate limiting, Docker containerization, responsive dashboard.
- Bounty cards include Fibonacci, API integration, CINE-50 video skill tasks, delivered template jobs, and high-value implementation tasks.

## Responsive Behavior
- Desktop: 3-column card grid.
- Tablet: 2-column grid.
- Mobile: 1-column grid, filter chips wrap, action row stacks.
