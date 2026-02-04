Generate a monitoring dashboard configuration for project metrics visualization.

## Steps

1. Determine the dashboard platform (Grafana, Datadog, custom HTML).
2. Identify key metrics to display:
   - **Build health**: CI pass rate, build duration trend.
   - **Code velocity**: Commits per day, PRs merged per week.
   - **Quality**: Test coverage trend, bug count, tech debt items.
   - **Performance**: API response times, error rates, uptime.
   - **Dependencies**: Outdated count, vulnerability count.
3. Design panel layout:
   - Top row: Key KPIs as single-stat panels.
   - Middle: Time series charts for trends.
   - Bottom: Tables for detailed breakdowns.
4. Configure data sources and queries for each panel.
5. Set up alert thresholds on critical metrics.
6. Export the dashboard configuration as JSON.

## Format

```json
{
  "title": "<Project> Dashboard",
  "panels": [
    { "type": "stat", "title": "Build Status", "query": "..." },
    { "type": "graph", "title": "Response Time (P95)", "query": "..." }
  ]
}
```

## Rules

- Keep dashboards focused with 8-12 panels maximum.
- Use consistent color coding: green=healthy, yellow=warning, red=critical.
- Include time range selector defaulting to last 24 hours.
- Add drill-down links from summary panels to detail views.
- Document the data source requirements for each panel.
