#!/bin/bash
# Blocks prompts that appear to contain secrets or credentials.
input=$(cat)

# Patterns that suggest leaked credentials
if echo "$input" | grep -qiE '(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|api[_-]?key\s*[:=]\s*["\x27]?[A-Za-z0-9]{16,})'; then
  echo '{
    "continue": false,
    "user_message": "This prompt appears to contain a secret or API key. Remove it and use environment variables instead."
  }'
  exit 0
fi

echo '{ "continue": true }'
exit 0
