---
name: yocto-commit-message
description: Use when creating, rewriting, reviewing, or splitting commits for meta-k230 or other Yocto/OpenEmbedded layers so commit subjects, bodies, trailers, and patch-series history follow Yocto/OpenEmbedded contribution conventions.
---

# Yocto Commit Message

Use Yocto/OpenEmbedded contribution conventions before committing or rewriting
history in this repository.

## Workflow

1. Split unrelated work into separate commits. Add each new recipe in its own
   commit. Keep an image/packagegroup change separate from adding the recipe
   unless one is meaningless without the other.
2. Choose the subject prefix from the recipe name when changing a recipe, or
   from the short path/component when changing repository documentation or
   tooling. Check nearby history with `git log --oneline <paths>`.
3. Write the subject as `<prefix>: <imperative summary>`.
4. Add a body when the subject is not enough. Explain what changed, why, the
   approach used, and relevant testing.
5. Do not add AI attribution, `AI-Generated`, `Co-Authored-By`, Claude, or
   agent-generated footer lines.
6. Read the sign-off identity from `git config user.name` and
   `git config user.email`; stop and ask the user to configure Git if either is
   missing.
7. End with exactly `Signed-off-by: Name <email>`, taking `Name` from
   `git config user.name` and `email` from `git config user.email`.
   Use `git commit -s`, or add that trailer manually when scripting commits.
8. Re-check `git log --format=fuller -n <count>` before pushing.

## Subject Rules

- Use the recipe name for recipe files: `fastfetch: Add recipe`.
- Use the packagegroup name for packagegroup changes:
  `packagegroup-k230-common: Add fastfetch`.
- Use the short path for repository-only agent guidance:
  `agents: Add Yocto commit message skill`.
- Keep the subject single-line, specific, and concise.
- Do not use Conventional Commit prefixes such as `feat:` or `fix:` unless the
  layer already uses them.

## Body Rules

Include the body for non-trivial changes:

```text
<prefix>: <summary>

Explain the problem or gap.

Explain the change and why this approach fits the layer.

Testing:
- <command or runtime validation>

Signed-off-by: $(git config user.name) <$(git config user.email)>
```

Use `Fixes [YOCTO #bug-id]` in the body only when there is a real Yocto
Bugzilla ID.

## Reference

Primary source: Yocto Project and OpenEmbedded Contributor Guide, "Preparing
Changes for Submission":

- Single commits per change.
- Summary prefixes should be the recipe name or short file path.
- Commit bodies should describe what, why, approach, and testing.
- This repository's `AGENTS.md` overrides generic AI-label guidance: use only
  the Git-configured Signed-off-by trailer above.
