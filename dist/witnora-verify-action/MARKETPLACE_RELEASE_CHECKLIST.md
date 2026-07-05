# Marketplace Release Checklist

1. Create public repo `joeyst8/witnora-verify-action`.
2. Copy `dist/witnora-verify-action/*` to the repository root.
3. Confirm `action.yml` is at the repository root.
4. Confirm `README.md` and `LICENSE` are present.
5. Commit and push the repository.
6. Push tag `v1`.
7. Create a GitHub Release for `v1`.
8. Check the GitHub Marketplace publish prompt.
9. Accept the Marketplace Developer Agreement if required.
10. Verify the action appears in Marketplace.
11. Test usage:

```yaml
uses: joeyst8/witnora-verify-action@v1
```
