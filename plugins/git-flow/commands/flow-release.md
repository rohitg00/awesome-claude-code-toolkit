Complete a feature/bugfix/hotfix flow by merging back to the target branch.

## Steps

1. Detect the current branch type from the prefix (feature/, bugfix/, hotfix/).
2. Run pre-merge checks:
   - All tests pass.
   - No merge conflicts with the target branch.
   - Branch is up to date with the target.
3. Determine the merge target:
   - feature/bugfix: merge to `develop` or `main`.
   - hotfix: merge to both `main` and `develop`.
4. Create a pull request if one does not exist:
   - `gh pr create --base <target> --title "<type>: <description>"`.
5. If auto-merge is requested:
   - Rebase on target: `git rebase origin/<target>`.
   - Merge with no-ff: `git merge --no-ff <branch>`.
   - Tag if hotfix: `git tag -a v<version> -m "Hotfix: <description>"`.
6. Clean up: delete the feature branch locally and remotely.
7. For hotfix, cherry-pick to develop if not merged there.

## Format

```
Flow completed:
  Branch: <branch-name>
  Merged to: <target-branch>
  PR: <url>
  Tag: <tag if hotfix>
  Cleanup: branch deleted

Changes:
  - <N> commits, <N> files changed
```

## Rules

- Never merge without passing tests and CI checks.
- Use `--no-ff` merges to preserve branch history in the merge graph.
- Tag hotfix releases immediately after merging to main.
- Ensure hotfix changes also reach the develop branch.
- Confirm before deleting branches with unmerged commits.
