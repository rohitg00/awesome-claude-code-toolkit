Stage, commit, and push changes with an auto-generated conventional commit message.

## Steps


1. Run `git status` to see all modified, staged, and untracked files.
2. Run `git diff` to review all changes (staged and unstaged).
3. Analyze the changes to determine the commit type:
4. Generate a conventional commit message:
5. Stage the appropriate files (avoid staging secrets or build artifacts).
6. Create the commit with the generated message.
7. Push to the remote branch with `git push origin HEAD`.

## Format


```
type(scope): description

Why: <explanation of motivation>
Refs: #<issue number> (if applicable)
```


## Rules

- Never commit .env files, credentials, or API keys.
- Commit message subject must be under 72 characters.
- Use present tense in commit messages ("add feature" not "added feature").

