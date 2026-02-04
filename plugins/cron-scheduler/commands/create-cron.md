# /create-cron - Create Cron Job

Configure a cron job with proper scheduling and error handling.

## Steps

1. Ask the user for the task description and desired schedule
2. Translate the schedule description to cron syntax (minute hour day month weekday)
3. Show the next 5 execution times to verify the schedule is correct
4. Create the cron job script with proper error handling and logging
5. Add a lock mechanism to prevent overlapping executions
6. Configure output redirection: stdout to log file, stderr to error log
7. Add environment variable setup at the top of the cron script
8. Set up email or webhook notification for job failures
9. Add a health check: alert if the job has not run within expected interval
10. Install the cron job using crontab or systemd timer
11. Verify the job is listed in the cron table
12. Document the job: purpose, schedule, log location, notification settings

## Rules

- Always use absolute paths in cron scripts (PATH is minimal in cron)
- Set a timeout to kill hung jobs (use timeout command)
- Use file locking (flock) to prevent overlapping executions
- Redirect output to log files; do not rely on cron mail
- Include the full environment setup in the script (PATH, HOME, etc.)
- Add a comment line above each cron entry describing its purpose
- Test the cron script manually before installing it
