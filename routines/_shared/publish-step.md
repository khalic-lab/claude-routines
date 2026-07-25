### 1. Write the brief

Use the Write tool to write the brief BODY to `_posts/{YYYY-MM-DD}-{slug}.md`, starting at the `#` heading from the Format block above. The front matter is derived at publish — don't write it yourself.

### 2. Publish — one command

```bash
python3 tools/publish.py --slug {slug} --date {YYYY-MM-DD} \
  --final /tmp/final.json --notify-body "{teaser}"
```
