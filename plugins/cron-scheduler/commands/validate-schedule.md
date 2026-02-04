# /validate-schedule - Validate Cron Schedule

Validate and explain a cron schedule expression.

## Steps

1. Take the cron expression from the user (5 or 6 fields)
2. Parse each field: minute, hour, day of month, month, day of week
3. Validate syntax: check for valid ranges, step values, and special characters
4. Detect common mistakes: day/month confusion, 0-indexed vs 1-indexed weekdays
5. Translate the expression to plain English description
6. Calculate the next 10 execution times based on the current date
7. Calculate the frequency: how many times per day, week, month
8. Identify potential issues: running too frequently, not running at expected times
9. Check for timezone considerations and DST transition impacts
10. Suggest alternative expressions if the schedule could be simplified
11. Compare with common cron presets: @hourly, @daily, @weekly, @monthly
12. Display a visual calendar showing execution times for the next 30 days

## Rules

- Support both 5-field (standard) and 6-field (with seconds) cron formats
- Validate ranges: minutes (0-59), hours (0-23), days (1-31), months (1-12), weekdays (0-7)
- Handle both numeric and named values for months and weekdays
- Warn about expressions that run more than 100 times per day
- Note timezone implications for jobs that span midnight or DST boundaries
- Detect mutually exclusive day-of-month and day-of-week combinations
- Support extended cron syntax: L (last), W (weekday), # (nth weekday)
