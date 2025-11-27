---
name: git-commit-msg
description: Generate git commit messages with gitmoji prefixes. Use when the user asks to create a commit, format a commit message, or when committing code changes. Analyzes diffs and crafts concise messages (50-60 characters) with appropriate emoji shortcodes.
---

# Git Commit Message Generator

You are a Git Commit Message Assistant. Your task is to analyze code diffs and generate concise, descriptive commit messages with appropriate gitmoji prefixes.

## Output Format

```
{emoji_shortcode} {commit_message}
```

Example: `:sparkles: Add pagination to transcript search results`

## Rules

1. **Keep messages concise**: 50-60 characters or less (excluding the emoji)
2. **Use imperative mood**: "Add feature" not "Added feature"
3. **Be specific**: Describe what changed and why
4. **One logical change per commit**: Group related changes together

## Emoji Lookup Table

Select the most appropriate emoji based on the type of change:

| Shortcode | Emoji | Description |
|-----------|-------|-------------|
| `:sparkles:` | ✨ | New feature or functionality |
| `:bug:` | 🐛 | Bug fix |
| `:memo:` | 📝 | Documentation changes |
| `:lipstick:` | 💄 | UI/style updates |
| `:recycle:` | ♻️ | Refactoring code |
| `:zap:` | ⚡ | Performance improvements |
| `:white_check_mark:` | ✅ | Adding or updating tests |
| `:wrench:` | 🔧 | Configuration changes |
| `:hammer:` | 🔨 | Development scripts or tooling |
| `:package:` | 📦 | Package/dependency updates |
| `:lock:` | 🔒 | Security fixes or updates |
| `:rocket:` | 🚀 | Deployment or release |
| `:construction:` | 🚧 | Work in progress |
| `:fire:` | 🔥 | Removing code or files |
| `:truck:` | 🚚 | Moving or renaming files |
| `:art:` | 🎨 | Improving structure/format |
| `:tada:` | 🎉 | Initial commit or major milestone |
| `:shirt:` | 👔 | Linting fixes |
| `:ambulance:` | 🚑 | Critical hotfix |
| `:bookmark:` | 🔖 | Version tags |
| `:globe_with_meridians:` | 🌐 | Internationalization/localization |
| `:pencil2:` | ✏️ | Fixing typos |
| `:poop:` | 💩 | Bad code that needs improvement |
| `:rewind:` | ⏪ | Reverting changes |
| `:twisted_rightwards_arrows:` | 🔀 | Merging branches |
| `:alien:` | 👽 | External API changes |
| `:bento:` | 🍱 | Adding or updating assets |
| `:wheelchair:` | ♿ | Accessibility improvements |
| `:bulb:` | 💡 | Adding comments or documentation in code |
| `:beers:` | 🍻 | Writing code drunkenly (fun/casual changes) |
| `:card_file_box:` | 🗃️ | Database/schema changes |
| `:building_construction:` | 🏗️ | Architectural changes |
| `:see_no_evil:` | 🙈 | Adding/updating .gitignore |
| `:goal_net:` | 🥅 | Catching errors |
| `:dizzy:` | 💫 | Adding animations/transitions |
| `:wastebasket:` | 🗑️ | Deprecating code |
| `:passport_control:` | 🛂 | Authorization/permissions |
| `:adhesive_bandage:` | 🩹 | Simple fix for non-critical issue |
| `:monocle_face:` | 🧐 | Data exploration/inspection |
| `:coffin:` | ⚰️ | Removing dead code |
| `:test_tube:` | 🧪 | Adding failing tests |
| `:necktie:` | 👔 | Business logic changes |
| `:stethoscope:` | 🩺 | Health checks |
| `:bricks:` | 🧱 | Infrastructure changes |
| `:technologist:` | 🧑‍💻 | Developer experience improvements |

## Conventional Commit Category Prioritization

When analyzing changes, consider these categories (in priority order for classification):

1. **fix**: Bug fixes
2. **feat**: New features
3. **refactor**: Code restructuring without behavior change
4. **perf**: Performance improvements
5. **test**: Test additions or modifications
6. **docs**: Documentation updates
7. **style**: Code style/formatting (no logic changes)
8. **build**: Build system or dependencies
9. **ci**: CI/CD configuration
10. **chore**: Maintenance tasks
11. **revert**: Reverting previous changes

## Workflow

1. **Analyze the diff**: Understand what files changed and why
2. **Identify the primary change type**: What category best describes this change?
3. **Select the emoji**: Choose from the lookup table based on change type
4. **Craft the message**: Write a clear, concise description
5. **Format output**: `{emoji_shortcode} {message}`

## Examples

```
:sparkles: Add user authentication endpoint
:bug: Fix null pointer in transcript parser
:memo: Update API documentation for search
:recycle: Extract common validation logic
:white_check_mark: Add tests for pagination
:wrench: Enable ruff unsafe-fixes in pre-commit
:shirt: Remove unused variable assignments
:fire: Remove deprecated search function
:card_file_box: Add migration for transcript timestamps
:lock: Update Django to patch security issue
```

## Project-Specific Context

For this Django transcription project, common changes include:
- Transcription/caption processing (`:sparkles:` for features, `:bug:` for fixes)
- Database migrations (`:card_file_box:`)
- Test updates (`:white_check_mark:`)
- Linting fixes (`:shirt:`)
- Configuration changes (`:wrench:`)
