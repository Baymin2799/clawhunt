# Studio Tabs Specification

## Overview
- Target file: `src/App.tsx`
- Screenshots: `docs/design-references/studio-tabs/*.png`
- Source URL: `https://clawhunt.store/studio`
- Interaction model: left workbench navigation switches local panels; `聊天` opens a SuperClaw chat workspace with a back action.

## Extracted Menu
- SuperClaw: live workbench hero, prompt capsule, category chips, open bounty feed.
- 聊天: SuperClaw delivery engine, suggestions, composer, model pill, open bounty side feed.
- 我的工作: task-control style dashboard with real-time activity, telemetry and delivery evidence.
- 订单: bounty/order escrow table with review and settlement states.
- 智能体: Agent hub cards for SuperClaw sub-agents and capability routing.
- 能力工坊: capability workshop / skill registry / delivery protocol cards.
- PaySwitch: Neural Wallet with Stripe, MetaMask and Phantom payment options.
- 套餐: free trial and paid SuperClaw plan comparison.
- 使用情况: usage and cost tracking for conversations, routes, verification and assets.

## Visual Notes
- Uses the same dark navy shell, grid background, translucent cards, blue/green borders, JetBrains Mono metrics and Space Grotesk headings as the original studio route.
- Chat panel follows extracted text: `SuperClaw 交付引擎`, `由 CLAUDE 驱动`, `工作区`, `登录后获得 1 次 SuperClaw 免费对话`, `浏览开放赏金`.
- PaySwitch follows extracted wallet text: `Neural Wallet`, `Your Wallet`, `$0.00`, `Deposit with Stripe`, `MetaMask`, `Phantom`.
- Usage/work panels follow extracted dashboard text: `任务控制`, `实时活动仪表盘`, `Agent 遥测`, `自动刷新`.

## Responsive Behavior
- Desktop: sidebar + main content; chat uses two columns; cards use 2-4 column grids depending on panel.
- Tablet: sidebar becomes horizontal scroll, main panels collapse to one or two columns.
- Mobile: all panel grids stack; order table becomes card rows; chat composer stacks vertically.
