# DiscoverAgentsHubPage Specification

## Overview
- **Target file:** `src/App.tsx`
- **Screenshot:** `docs/design-references/discover/agents-hub-original-full.png`
- **Extraction:** `docs/research/clawhunt-discover-agents-hub-extraction.json`
- **Interaction model:** static unauthenticated visible Chat Hub clone

## DOM Structure
- Left sidebar: 能力研讨会, 代理团队, 新对话, SuperClaw agent entries, search placeholder, project box, credit button.
- Main chat console: SuperClaw header, empty state, prompt suggestions, composer.
- Right rail: open bounty cards.

## Text Content
SuperClaw 交付引擎; 选择下面的建议，或输入你自己的消息开始。统一 SuperClaw 引擎。

## Responsive Behavior
- Desktop: sidebar + console + bounty rail.
- Tablet/mobile: sidebar stacks above chat and right rail stacks below.
