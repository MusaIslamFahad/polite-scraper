# Rematch prompt (v2) — same request, four specific fixes added

Everything from the first prompt, PLUS these four things I learned I'd left out after finding real
bugs when I actually ran the first version:

1. **Some books may have no description at all.** Don't assume the description block is always
   there — if it's missing, store `null` for that field instead of crashing.

2. **Not every failure deserves a retry.** A 404 means the page doesn't exist — retrying it wastes
   time and requests. A 403 means the site said no — retrying makes it worse. Only retry on
   timeouts and 5xx server errors.

3. **A rerun should refresh existing books, not just skip them.** If a book's price or rating
   changes on the site, running the scraper again should pick that up — don't just check "have I
   seen this URL before" and skip it forever once it's in the file.

4. **Every request needs an explicit timeout** so a hung connection can't freeze the whole run.

Same output format, same JSON file, same "first 3 pages only" scope.
