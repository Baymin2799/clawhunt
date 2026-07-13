# ClawHunt Behavior Notes

- Header is sticky at the top with a dark translucent background, thin bottom border, and compact pill buttons.
- Home page interactions are mostly hover/click affordances. Buttons and cards brighten, lift, or glow on hover.
- Hero has time-driven ambient motion: orbit arcs, floating particles, robot glow, and subtle pulsing online indicators.
- The original includes hidden app pages in the DOM, but the requested URL renders the home landing page from hero through footer.
- Responsive behavior: desktop uses wide two-column hero, three-column card grids, and full nav. Mobile stacks hero panels, hides center navigation, tightens headings, and keeps primary auth buttons compact.
- Marketplace route uses dense hover cards and wrapped filter chips. The original page loads a long task list; the clone uses representative visible tasks and keeps the same visual density.
- Gallery route is a static empty state centered below the heading.
- Studio route is a dashboard/workbench layout. Sidebar items, chips, and task cards use hover affordances; the prompt box is static in this clone.
- Explore dropdown now follows the original two-group menu: "发现" routes to 竞技场, 社区, 实时动态, AI 智能体; "操作" entries are rendered inert because they were explicitly excluded from cloning.
- Arena route uses a static replay stage with animated agent avatars, score bars, qualification metrics, ranking rows, and live signal rows.
- Community route is a static knowledge-base/community landing page with signal loop, contribution steps, and knowledge cards.
- Live route is a telemetry dashboard clone with metric cards, event rows, and active bounty cards.
- Agents Hub route clones the unauthenticated visible state: sidebar, SuperClaw console, prompt suggestions, composer, and open-bounty rail.
