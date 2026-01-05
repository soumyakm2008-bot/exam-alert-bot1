import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import pdfplumber
import urllib.parse
import re

# ================= CONFIG =================
BOT_TOKEN = "7700793414:AAGYtiWGj2OPTpl2deM2GHQ_6KFiNg1wX0Q"
CHAT_ID = "6765878478"

EXAMS = {
    "JEE Main": "https://jeemain.nta.nic.in",
    "NEET": "https://neet.nta.nic.in",
    "CUET UG": "https://cuet.nta.nic.in",
    "OJEE": "https://ojee.nic.in",
    "NEST": "https://www.nestexam.in",
    "IISER IAT": "https://iiseradmission.in",
    "VITEEE": "https://viteee.vit.ac.in",
    "MET": "https://manipal.edu",
    "COMEDK": "https://www.comedk.org",
    "MHT-CET": "https://cetcell.mahacet.org",
    "WBJEE": "https://wbjeeb.nic.in"
}

KEYWORDS = [
    "registration", "apply online", "application form",
    "admission", "start date", "apply now", "filling of form"
]

DATA_DIR = Path("seen_exams")
DATA_DIR.mkdir(exist_ok=True)

# ==========================================
def send_alert(exam_name, link, source_type):
    message = (
        f"🚨 {exam_name} 2026 Registration Alert!\n\n"
        f"Detected that registration/application has started.\n"
        f"Source Type: {source_type}\n"
        f"Link: {link}\n"
        f"Time: {datetime.now()}"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

# ==========================================
def check_pdf(url):
    try:
        response = requests.get(url, timeout=20)
        pdf_path = Path("temp.pdf")
        with open(pdf_path, "wb") as f:
            f.write(response.content)

        text_combined = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_combined += page_text.lower() + "\n"

        # Check for keywords and 2026 mention
        for kw in KEYWORDS:
            if re.search(rf"{kw}.*2026|2026.*{kw}", text_combined):
                return True
        return False
    except:
        return False

# ==========================================
def check_website(url):
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text().lower()
            if any(kw in href.lower() or kw in text for kw in KEYWORDS):
                if "2026" in href.lower() or "2026" in text:
                    return urllib.parse.urljoin(url, href)
        # Also scan page text
        page_text = soup.get_text().lower()
        if any(f"{kw} 2026" in page_text or f"2026 {kw}" in page_text for kw in KEYWORDS):
            return url
        return None
    except:
        return None

# ==========================================
def main():
    for exam, url in EXAMS.items():
        seen_file = DATA_DIR / f"{exam}.txt"
        seen = set(seen_file.read_text().splitlines()) if seen_file.exists() else set()

        # 1️⃣ Check PDFs on the page
        try:
            response = requests.get(url, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")
            for a in soup.find_all("a", href=True):
                link = urllib.parse.urljoin(url, a["href"])
                if link.endswith(".pdf") and link not in seen:
                    if check_pdf(link):
                        send_alert(exam, link, "PDF")
                        seen.add(link)
        except:
            pass

        # 2️⃣ Check webpage text / HTML links
        website_alert = check_website(url)
        if website_alert and website_alert not in seen:
            send_alert(exam, website_alert, "Webpage")
            seen.add(website_alert)

        # Update seen list
        seen_file.write_text("\n".join(seen))

# ==========================================
if __name__ == "__main__":
    main()
