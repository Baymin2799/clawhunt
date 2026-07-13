# Studio Page Specification

## Overview
- Target: `src/App.tsx` studio route.
- Screenshot: `docs/design-references/clawhunt-studio-original-viewport.png`.
- Source URL: `https://clawhunt.store/studio`.
- Interaction model: static dashboard clone with hoverable nav, chips, and cards.

## Extracted Structure
- Sticky global header with nav: 首页, 市场, 交付画廊, 工作台, 探索, 资源.
- Left workbench sidebar: SuperClaw, 聊天, 我的工作, 订单, 智能体, 能力工坊, PaySwitch, 套餐, 使用情况.
- Main hero: online badge, large headline "想让我们交付什么？", short description.
- Prompt bar with placeholder and blue send button.
- Suggestion chips: 修复失败的 CI 流水线, 构建 REST 到 GraphQL 网关, 优化慢速 Postgres 查询, 设计一个定价页.
- Category pills: all, frontend, backend, 全栈, data, design, devops.
- Latest delivery grid: 3 columns of task cards with tags, status, title, description, bid stats, like count, and "接单" button.

## Exact Visual Notes
- Fullscreen studio shell: deep navy/black background with fine grid overlay.
- Sidebar width about 248px with highlighted SuperClaw item.
- Hero uses very large white text with blue accent on "交付".
- Prompt bar is a wide rounded capsule with dark fill and blue send button.
- Task cards are dense, semi-transparent panels with blue borders and small rounded tags.

## Responsive Behavior
- Desktop: sidebar + main grid.
- Tablet/mobile: sidebar becomes horizontal/stacked navigation, cards collapse to one column.
