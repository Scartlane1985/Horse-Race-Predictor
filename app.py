import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
import re
from pathlib import Path

st.set_page_config(page_title="Horse Race Predictor", layout="centered")
st.title("🏇 Horse Race Predictor (Live Scraper)")

st.markdown("""
Paste a live racecard URL from [AtTheRaces](https://www.attheraces.com/racecards), for example:
```
https://www.attheraces.com/racecard/Southwell/28-March-2025/1640
```
""")

race_url = st.text_input("Enter ATR race URL:")

# --- FORM SCRAPER ---
def get_form_figures(context, form_url):
    full_url = f"https://www.attheraces.com{form_url}"
    page = context.new_page()
    st.write(f"🔍 Scraping form: {full_url}")

    form_figures = []
    try:
        page.goto(full_url, timeout=15000)
        page.wait_for_selector("#tab-form-flat-form .panel-content p.p--medium", timeout=10000)
        digits_html = page.inner_html("#tab-form-flat-form .panel-content p.p--medium")
        form_figures = re.findall(r"\\d+", digits_html)
        result = ''.join(form_figures[-6:]) if form_figures else "N/A"
    except Exception as e:
        st.warning(f"❌ Form scrape failed for {form_url}: {e}")
        result = "N/A"

    horse_id = form_url.split("/")[-1]
    debug_path = Path(f"horse_debug_{horse_id}.html")
    with open(debug_path, "w", encoding="utf-8") as f:
        f.write(page.content())
    st.write(f"📝 Debug HTML saved: {debug_path}")

    page.close()
    return result

# --- MAIN SCRAPER ---
def scrape_atr_runners(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        browser_context = browser.new_context()
        page = browser_context.new_page()
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        st.success(f"✅ Page loaded: {page.title()}")

        try:
            page.locator("button:has-text('Accept All Cookies')").click(timeout=3000)
        except:
            pass

        try:
            page.wait_for_selector('.odds-grid__row--horse', timeout=15000)
        except:
            st.error("❌ Race data not found.")
            browser.close()
            return []

        html = page.content()
        with open("atr_page_dump.html", "w", encoding="utf-8") as f:
            f.write(html)
        st.write("✅ HTML saved to atr_page_dump.html")

        runners = []
        rows = page.query_selector_all('.odds-grid__row--horse')
        for row in rows:
            try:
                horse_tag = row.query_selector('.odds-grid-horse__jockey a')
                horse_name = horse_tag.inner_text().strip() if horse_tag else "N/A"
                horse_link = horse_tag.get_attribute("href") if horse_tag else None

                jockey_tag = row.query_selector('.odds-grid-horse__name')
                jockey = jockey_tag.inner_text().strip() if jockey_tag else "N/A"

                if horse_name != "N/A" and horse_link and jockey != "N/A":
                    form = get_form_figures(context=browser_context, form_url=horse_link)
                    runners.append({
                        "Horse": horse_name.replace('\xa0', ' '),
                        "Jockey": jockey.replace('\xa0', ' '),
                        "Form": form
                    })
            except Exception as e:
                st.warning(f"⚠️ Skipping runner due to error: {e}")
                continue

        browser.close()
        return runners

# --- RUN ---
if race_url:
    with st.spinner("Scraping live race data..."):
        runner_data = scrape_atr_runners(race_url)

    if runner_data:
        df = pd.DataFrame(runner_data)
        df["FormScore"] = df["Form"].apply(lambda x: sum([5 if c == '1' else 3 if c == '2' else 1 if c == '3' else 0 for c in x]) if x != "N/A" else 0)
        df = df.sort_values(by="FormScore", ascending=False).reset_index(drop=True)

        st.subheader("🏁 Runners Ranked by Form")
        st.dataframe(df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download CSV", csv, "race_prediction.csv", "text/csv")
    else:
        st.error("No runners extracted. Please check the URL.")
