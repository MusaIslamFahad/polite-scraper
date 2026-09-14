# The prompt (written from memory, not from the assignment PDF)

This is the prompt I gave the AI for the "rematch" — written from what I remembered building,
not by re-reading the assignment. That's the point of this exercise: see what I forgot to say.

---

Build me a Python web scraper for books.toscrape.com, a public scraping sandbox. I only want the
first 3 pages of the catalogue (that's 60 books total), not the whole site.

For each book, get:
- title
- price
- how many are in stock
- star rating
- description
- what page I found it on and when I scraped it

Requirements:
- Send a proper User-Agent so I'm not anonymous, and don't hammer the site — wait a bit between
  requests and cache pages locally so I'm not re-downloading during dev.
- Turn the price like "£51.77" into an actual number.
- Check the data is valid before saving it (e.g. price should be a number, URL should be a real
  URL) — bad records shouldn't end up in the final file.
- If a page fails to load, don't let it crash the whole run — just skip it and note it somewhere.
- Save everything to a JSON file. Running it twice shouldn't give me double the books.
- At the end, print/save a short summary of how the run went — how many pages, how many worked,
  how many failed.

Give me working Python code, structured however makes sense to you.
