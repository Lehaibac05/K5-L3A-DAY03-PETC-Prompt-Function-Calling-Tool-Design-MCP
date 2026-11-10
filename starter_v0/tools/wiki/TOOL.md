---
name: wiki
track: bonus
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [title, lang]
outputs: [status, title, summary, url]
side_effect: false
---
# wiki

Returns the lead summary of a Wikipedia article for background / definitions.
Not for news or recent events (use `lookup`).