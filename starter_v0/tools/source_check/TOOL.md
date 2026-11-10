---
name: source_check
track: core
kind: local_formatter
provider: local
requires_env: []
inputs: [urls, require_https]
outputs: [valid, unique, invalid, duplicates, summary]
side_effect: false
---
# source_check

Validates a list of source URLs locally. It reports malformed/non-HTTPS links,
normalizes fragments, and identifies duplicate URLs. It never fetches a URL or
makes a network request.
