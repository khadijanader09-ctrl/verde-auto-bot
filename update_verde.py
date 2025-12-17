import cloudscraper
from bs4 import BeautifulSoup
import feedparser
import os
import datetime
import re
import random
import json

# --- CONFIGURATION ---
MY_SITE_URL = "https://verdevoice.com"
# On vise large : Global News + Environment (pour coller à la ligne édito)
AUTHORITY_RSS = "https://news.google.com/rss/search?q=world+news+environment+technology&hl=en-US&gl=US&ceid=US:en"
OUTPUT_FILE = "public/index.html"

# Images à bannir
EXCLUDED_IMGS = ["placeholder", "logo.svg", "default", "blank", "1x1", "pixel"]

# BANQUE D'IMAGES (Thème : Monde / Nature / Tech Verte)
THEMATIC_IMAGES = [
    "https://images.unsplash.com/photo-1502082553048-f009c37129b9?auto=format&fit=crop&w=600&q=80", # Nature Tree
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=600&q=80", # Globe Tech
    "https://images.unsplash.com/photo-1497436072909-60f360e1d4b0?auto=format&fit=crop&w=600&q=80", # Green City
    "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?auto=format&fit=crop&w=600&q=80", # City Night
    "https://images.unsplash.com/photo-1466611653911-95081537e5b7?auto=format&fit=crop&w=600&q=80", # Wind Energy
    "https://images.unsplash.com/photo-1581093450021-4a7360e9a6b5?auto=format&fit=crop&w=600&q=80", # Lab Tech
    "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=600&q=80"  # Fields
]
FALLBACK_IMG = "https://verdevoice.com/assets/logo.png" # Ou une image générique verte

# SEO
SEO_DESC = "VerdeVoice - Latest global news, technology updates and sustainable future reports."
SEO_KEYWORDS = "global news, environment, technology, verdevoice, international updates, sustainability"

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})

FOUND_CATEGORIES = {}

def clean_html(raw_html):
    if not raw_html: return ""
    cleanr = re.compile('<.*?>')
    text = re.sub(cleanr, '', raw_html)
    return text[:140] + "..."

def get_external_news(rss_url, limit=6):
    print(f"   -> 🌍 Google News...")
    try:
        response = scraper.get(rss_url)
        feed = feedparser.parse(response.content)
        links = []
        if not feed.entries: return []

        for entry in feed.entries:
            img_src = random.choice(THEMATIC_IMAGES)
            desc = clean_html(entry.description) if hasattr(entry, 'description') else ""
            
            links.append({
                'title': entry.title, 
                'link': entry.link, 
                'img': img_src, 
                'desc': desc,
                'source': 'Global News',
                'category': 'World', # Catégorie par défaut pour externe
                'cat_link': f"{MY_SITE_URL}/news_en.html",
                'is_mine': False,
                'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            if len(links) >= limit: break
        return links
    except Exception as e:
        print(f"      [!] Erreur Google: {e}")
        return []

def get_my_links():
    print(f"   -> 🏠 VerdeVoice...")
    try:
        response = scraper.get(MY_SITE_URL)
        response.encoding = 'utf-8'
        
        if response.status_code != 200: return []

        soup = BeautifulSoup(response.text, 'html.parser')
        my_links = []
        
        # Cible spécifique VerdeVoice (art-card)
        cards = soup.find_all('article', class_='art-card')
        
        for card in cards:
            # Titre & Lien
            h2 = card.find(class_='art-h2')
            if not h2: continue
            link_tag = h2.find('a')
            if not link_tag: continue
            
            url = link_tag.get('href')
            if not url: continue
            if url.startswith('/'): url = MY_SITE_URL + url
            title = link_tag.get_text().strip()

            # Image
            thumb = card.find(class_='art-thumb')
            if not thumb: continue
            img_tag = thumb.find('img')
            if not img_tag: continue
            
            img_src = img_tag.get('src') or img_tag.get('data-src')
            if not img_src: continue
            if img_src.startswith('/'): img_src = MY_SITE_URL + img_src
            
            # Filtre images
            is_bad = False
            for bad in EXCLUDED_IMGS:
                if bad in img_src: is_bad = True
            if is_bad: continue

            # Catégorie (Spécifique VerdeVoice: class='cat-tag')
            cat_name = "News"
            cat_link_url = f"{MY_SITE_URL}/news_en.html"
            try:
                cat_elem = card.find(class_='cat-tag')
                if cat_elem:
                    cat_name = cat_elem.get_text().strip()
                    if cat_elem.name == 'a':
                        cat_link_url = cat_elem.get('href')
                        if cat_link_url and cat_link_url.startswith('/'):
                            cat_link_url = MY_SITE_URL + cat_link_url
                        FOUND_CATEGORIES[cat_name] = cat_link_url
            except: pass

            # Description
            desc_div = card.find(class_='art-desc')
            desc = ""
            if desc_div:
                txt = desc_div.get_text().strip()
                if len(txt) > 20: desc = txt[:140] + "..."

            # Date
            date_div = card.find(class_='art-date')
            date_txt = date_div.get_text().strip() if date_div else datetime.datetime.now().strftime("%Y-%m-%d")

            if not any(d['link'] == url for d in my_links):
                my_links.append({
                    'title': title, 
                    'link': url, 
                    'img': img_src,
                    'desc': desc,
                    'source': 'VerdeVoice',
                    'category': cat_name,
                    'cat_link': cat_link_url,
                    'is_mine': True,
                    'date': date_txt
                })

            if len(my_links) >= 6: break
        
        print(f"      > {len(my_links)} articles valides trouvés.")
        return my_links

    except Exception as e:
        print(f"      [!] Erreur scraping : {e}")
        return []

def generate_html():
    print("1. Génération Design VerdeVoice...")
    
    my_news = get_my_links()
    auth_news = get_external_news(AUTHORITY_RSS, limit=6)
    
    final_list = []
    if not my_news: my_news = []
    if not auth_news: auth_news = []
    
    max_len = max(len(my_news), len(auth_news))
    for i in range(max_len):
        if i < len(my_news): final_list.append(my_news[i])
        if i < len(auth_news): final_list.append(auth_news[i])

    now_str = datetime.datetime.now().strftime("%H:%M")
    year = datetime.datetime.now().year

    # Tags Dynamiques Footer
    tags_html = ""
    if not FOUND_CATEGORIES:
        FOUND_CATEGORIES["Latest News"] = f"{MY_SITE_URL}/news_en.html"
    
    for name, link in FOUND_CATEGORIES.items():
        tags_html += f'<a href="{link}" target="_blank" class="footer-tag">{name}</a>'

    # JSON-LD
    json_ld = {
        "@context": "https://schema.org",
        "@type": "NewsMediaOrganization",
        "name": "VerdeVoice News",
        "url": "https://verdevoice.com",
        "logo": "https://verdevoice.com/assets/logo.png"
    }

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VerdeVoice - Live Feed</title>
        <meta name="description" content="{SEO_DESC}">
        <meta name="keywords" content="{SEO_KEYWORDS}">
        <link rel="icon" href="https://verdevoice.com/assets/favicon.png">
        <script type="application/ld+json">{json.dumps(json_ld)}</script>
        
        <style>
            /* CSS VERDEVOICE ORIGINAL */
            :root {{ 
                --bg: #f5fcfb; --card: #ffffff; --text: #0f172a; 
                --muted: #64748b; --brand: #0f766e; --accent: #14b8a6; 
                --line: #e2e8f0; --shadow: 0 4px 6px -1px rgba(15, 118, 110, 0.1); 
            }}
            body {{ margin: 0; background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; line-height: 1.6; }}
            a {{ color: inherit; text-decoration: none; transition: .2s; }}
            a:hover {{ color: var(--brand); }}
            .container {{ max-width: 1000px; margin: 0 auto; padding: 0 15px; }}
            
            /* HEADER */
            header.site {{ background: var(--card); border-bottom: 3px solid var(--brand); padding: 10px 0; position:sticky; top:0; z-index:50; box-shadow: var(--shadow); }}
            .head-row {{ display: flex; justify-content: space-between; align-items: center; }}
            .brand {{ display: flex; align-items: center; gap: 10px; font-size: 1.5rem; font-weight: 800; color: var(--brand); text-transform: uppercase; }}
            .brand svg {{ width: 30px; height: 30px; fill: var(--brand); }}
            
            .lang-btns {{ display: flex; gap: 8px; }}
            .l-btn {{ display: inline-flex; justify-content: center; align-items: center; width: 35px; height: 35px; background: #fff; color: var(--brand); border: 2px solid var(--brand); font-weight: 700; border-radius: 4px; font-size: 0.8rem; }}
            .l-btn:hover {{ background: var(--brand); color: #fff; }}

            /* GRID & CARDS */
            .card-list {{ display: flex; flex-direction: column; gap: 20px; margin-top: 30px; }}
            
            /* DESIGN HORIZONTAL (Spécifique VerdeVoice) */
            .art-card {{ 
                display: flex; gap: 20px; background: var(--card); 
                border: 1px solid var(--line); border-radius: 8px; 
                overflow: hidden; box-shadow: var(--shadow); 
                height: 200px; /* Hauteur fixe pour uniformité */
            }}
            
            .art-thumb {{ width: 280px; flex-shrink: 0; position: relative; background:#eee; }} 
            .art-thumb img {{ width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s; }}
            .art-card:hover .art-thumb img {{ transform: scale(1.05); }}
            
            .art-info {{ padding: 20px; display: flex; flex-direction: column; justify-content: center; flex: 1; }}
            
            .cat-tag {{ 
                background: var(--brand); color: #fff; padding: 4px 8px; 
                font-size: 0.7rem; border-radius: 4px; text-transform: uppercase; 
                width: fit-content; margin-bottom: 8px; font-weight:bold;
            }}
            .tag-ext {{ background: var(--muted); }} /* Gris pour Google News */
            
            .art-h2 {{ margin: 0 0 10px 0; font-size: 1.3rem; line-height: 1.3; font-weight:700; }}
            
            .art-desc {{ 
                font-size: 0.95rem; color: var(--muted); opacity: 0.9; 
                margin-bottom: 10px; line-height: 1.5; 
                display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; 
            }}
            .art-desc:empty {{ display:none; }}

            .art-date {{ font-size: 0.8rem; color: var(--muted); margin-top: auto; display:flex; justify-content:space-between; }}

            /* MOBILE */
            @media (max-width: 700px) {{
                .art-card {{ flex-direction: column; height: auto; }}
                .art-thumb {{ width: 100%; height: 200px; }}
            }}

            /* FOOTER TAGS */
            .tags-section {{ margin-top: 50px; padding: 40px 20px; background: #f0fdfa; border-top: 1px solid var(--brand); text-align:center; }}
            .footer-tag {{ 
                display:inline-block; margin:5px; padding: 6px 14px; background: #fff; border: 1px solid var(--brand); 
                border-radius: 20px; font-size: 0.8rem; font-weight: 600; color: var(--brand);
            }}
            .footer-tag:hover {{ background: var(--brand); color: #fff; }}
        </style>
    </head>
    <body>

    <header class="site">
        <div class="container head-row">
            <a href="https://verdevoice.com" class="brand">
                <svg viewBox="0 0 24 24"><path d="M17,8C8,10 5.9,16.17 3.82,21.34L5.71,22L6.66,19.7C7.14,19.87 7.64,20 8,20C19,20 22,3 22,3C21,5 14,5.25 9,6.25C4,7.25 2,11.5 2,13.5C2,15.5 3.75,17.25 3.75,17.25C7,8 17,8 17,8Z"/></svg> 
                VerdeVoice
            </a>
            <div class="lang-btns">
                <a href="https://verdevoice.com/news_en.html" class="l-btn">EN</a>
                <a href="https://verdevoice.com/news_fr.html" class="l-btn">FR</a>
                <a href="https://verdevoice.com/news_es.html" class="l-btn">ES</a>
                <a href="https://verdevoice.com/news_ar.html" class="l-btn">AR</a>
            </div>
        </div>
    </header>

    <main class="container">
        <div style="margin: 30px 0; border-bottom: 2px solid var(--line); padding-bottom: 10px;">
            <span style="font-size: 1.5rem; font-weight: 800; color: var(--brand);">LIVE FEED</span>
            <span style="float:right; font-family:monospace; color:var(--muted);">{now_str} UTC</span>
        </div>

        <div class="card-list">
    """

    for item in final_list:
        fallback = random.choice(THEMATIC_IMAGES)
        cat_class = "cat-tag" if item['is_mine'] else "cat-tag tag-ext"
        
        html_content += f"""
        <article class="art-card">
            <div class="art-thumb">
                <a href="{item['link']}" target="_blank">
                    <img src="{item['img']}" alt="{item['title']}" loading="lazy" onerror="this.src='{fallback}'">
                </a>
            </div>
            <div class="art-info">
                <div>
                    <a href="{item['cat_link']}" class="{cat_class}" target="_blank">{item['category']}</a>
                </div>
                <h2 class="art-h2"><a href="{item['link']}" target="_blank">{item['title']}</a></h2>
                <div class="art-desc">{item['desc']}</div>
                <div class="art-date">
                    <span>{item['date']}</span>
                    <span>{item['source']}</span>
                </div>
            </div>
        </article>
        """

    html_content += f"""
        </div>
    </main>

    <div class="tags-section">
        <h4 style="color:var(--brand); text-transform:uppercase; margin-bottom:20px;">Trending Topics</h4>
        <div>{tags_html}</div>
        <p style="margin-top:30px; font-size:0.8rem; color:var(--muted);">© {year} VerdeVoice Global.</p>
    </div>

    </body>
    </html>
    """

    if not os.path.exists("public"):
        os.makedirs("public")
        
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("2. HTML VerdeVoice généré.")
    return True

if __name__ == "__main__":
    if generate_html():
        os.system("firebase deploy --only hosting")
