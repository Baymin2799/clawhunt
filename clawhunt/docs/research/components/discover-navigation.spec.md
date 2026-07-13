# DiscoverNavigation Specification

## Overview
- **Target file:** `src/App.tsx`
- **Interaction model:** hover/focus dropdown with click-to-route items
- **Source:** `https://clawhunt.store/arena`

## DOM Structure
- Top navigation item "探索" opens a floating dark dropdown.
- Group "发现" contains: 竞技场, 社区, 实时动态, AI 智能体.
- Group "操作" contains: 钱包, SuperClaw, Pay-Switch. These are shown as inert entries only because the user asked not to clone operation pages.

## Computed Styles
- Dropdown background: rgba(9, 13, 30, 0.96)
- Border: 1px solid rgba(0, 212, 255, 0.16)
- Radius: 10px
- Item height: 34px
- Active item background: rgba(0, 128, 200, 0.24)

## Text Content
发现 / 竞技场 / 社区 / 实时动态 / AI 智能体 / 操作 / 钱包 / SuperClaw / Pay-Switch

## Responsive Behavior
- Desktop: dropdown appears under the top navigation item.
- Tablet and mobile: top nav is hidden by the existing responsive header rule.
