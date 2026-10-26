# Putting the comic page online at comics.asherdesign.com

About 15 minutes of clicking. Everything is free. You won't need to type any
code. Claude handles the one technical step (uploading the files).

**What's involved, in plain terms**
- **GitHub** stores the page and shows it to visitors for free. It also runs
  the automatic price refresh every 6 hours. You already have an account from
  Shibuya: **kadugen**.
- **Hostinger** is where asherdesign.com is registered. You add one setting
  there so `comics.asherdesign.com` points to the page.

---

## Part 1: Create an empty home for the page on GitHub (2 min)

1. Go to **https://github.com/new** and sign in as **kadugen** if asked.
2. **Repository name:** type `comic-collection`
3. Choose **Public**. (Free hosting requires this. It only means people
   could see the page's files, which is the same information that's on the page.)
4. Leave everything else as it is. Don't tick any boxes.
5. Click the green **Create repository** button.
6. You'll see a page full of instructions. **Ignore them.** Tell Claude
   "the repo is created."

## Part 2: Claude uploads the files

Claude uploads the page and the first set of prices. When it's done, you'll be
told to continue.

## Part 3: Turn on the website (2 min)

1. Go to **https://github.com/kadugen/comic-collection/settings/pages**
2. Under **Build and deployment → Source**, choose **Deploy from a branch**.
3. Under **Branch**, choose **main**, leave the folder as **/ (root)**, and
   click **Save**.
4. Under **Custom domain**, type `comics.asherdesign.com` and click **Save**.
   It will say the DNS check failed. **That's expected.** Part 4 fixes it.

## Part 4: Point comics.asherdesign.com at the page (5 min)

This is the same kind of step you did for shibuya.asherdesign.com.

1. Log in to **Hostinger** → **Domains** → **asherdesign.com** →
   **DNS / Nameservers** (sometimes called **DNS Zone**).
2. Find **Add record** and fill it in:
   - **Type:** `CNAME`
   - **Name** (or Host): `comics`
   - **Points to** (or Target): `kadugen.github.io`
   - **TTL:** leave as is
3. Click **Add record** (or Save).

Your main website and the Shibuya site are not affected.

## Part 5: Wait, then switch on the secure padlock (5 min to 1 hour)

1. Wait 10–60 minutes for the internet to pick up the change.
2. Go back to **https://github.com/kadugen/comic-collection/settings/pages**
   and refresh the page. When it says *"Your site is live at
   comics.asherdesign.com"*, tick **Enforce HTTPS**. (If the box is greyed out,
   wait a bit longer and refresh.)
3. Visit **https://comics.asherdesign.com**. You're done.

---

## After it's live

**Prices update on their own** every 6 hours. You don't need to do anything.

**To add a comic:** add a row to your Google Sheet as usual. In the Link column,
paste the comic's ComicBookRealm series page. It appears on the website after
the next update (within 6 hours).

**To update prices right now:**
1. Go to **https://github.com/kadugen/comic-collection/actions**
2. Click **Update prices** on the left.
3. Click the **Run workflow** button on the right, then the green **Run workflow**.
4. Wait about a minute and refresh your comic page.

**If a comic shows a small "sheet" label** next to its name, the website
couldn't find it on ComicBookRealm and is using the value from your
spreadsheet. Ask Claude to fix the match.

**If you get an email from GitHub saying "Update prices failed":** one failure
now and then is harmless. If it keeps happening, ComicBookRealm may have changed
something. Ask Claude to take a look. The page keeps showing the last good
prices in the meantime.
