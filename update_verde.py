import requests
from bs4 import BeautifulSoup
import feedparser  # On utilise l'outil spécialisé pour le RSS externe
import os
import datetime
import random

# --- CONFIGURATION ---
MY_SITE_URL = "https://verdevoice.com"

# NOUVELLE SOURCE (Google News : Incassable et très haute autorité)
AUTHORITY_RSS = "https://news.google.com/rss/search?q=écologie+environnement&hl=fr&gl=FR&ceid=FR:fr"

OUTPUT_FILE = "public/index.html"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def get_external_news(rss_url, limit=3):
    """ Utilise feedparser pour lire le RSS externe de manière fiable """
    print(f"   -> Récupération du camouflage (Futura)...")
    try:
        # On utilise feedparser avec un User-Agent pour ne pas être bloqué
        feed = feedparser.parse(rss_url, agent=USER_AGENT)
        
        external_links = []
        
        if not feed.entries:
            print(f"      [!] Attention : Le flux externe semble vide ou bloqué.")
            return []

        for entry in feed.entries:
            # Nettoyage basique
            title = entry.title
            link = entry.link
            
            external_links.append({'title': title, 'link': link, 'is_mine': False})
            
            if len(external_links) >= limit:
                break
                
        print(f"      > {len(external_links)} articles externes trouvés.")
        return external_links
    except Exception as e:
        print(f"      [!] Erreur camouflage : {e}")
        return []

def get_my_links():
    """ Scrape TES articles via BeautifulSoup """
    print(f"   -> Récupération de tes articles (VerdeVoice)...")
    try:
        response = requests.get(MY_SITE_URL, headers={"User-Agent": USER_AGENT}, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        my_links = []
        potential_titles = soup.find_all(['h2', 'h3'])
        
        for title_tag in potential_titles:
            link_tag = title_tag.find('a')
            if link_tag and link_tag.get('href'):
                url = link_tag.get('href')
                text = link_tag.get_text().strip()
                
                if len(text) > 10:
                    my_links.append({'title': text, 'link': url, 'is_mine': True})
                
                if len(my_links) >= 5: # On prend 5 de tes articles
                    break
        
        print(f"      > {len(my_links)} de tes articles trouvés.")
        return my_links
    except Exception as e:
        print(f"      [!] Erreur scraping perso : {e}")
        return []

def generate_html():
    print("1. Construction du Mix SEO (Hybride)...")
    
    my_news = get_my_links()
    auth_news = get_external_news(AUTHORITY_RSS, limit=4) 
    
    if not my_news:
        print("ERREUR CRITIQUE : Tes articles sont introuvables.")
        return False

    # --- MÉLANGE INTELLIGENT ---
    # Si on a des news externes, on fait le sandwich. 
    # Sinon, on met juste les tiennes (plan B).
    if len(auth_news) >= 2:
        final_list = auth_news[:2] + my_news + auth_news[2:]
    else:
        final_list = my_news
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="google-site-verification" content="oeHmZmpFuk822bvs-DMKLdUons-NklXRos4dn6-tw4Y" />
        <title>Verde News : L'actualité Verte en Continu</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }}
            h1 {{ color: #2e7d32; border-bottom: 3px solid #81c784; padding-bottom: 10px; }}
            .article {{ margin-bottom: 15px; padding: 15px; border-radius: 8px; transition: transform 0.2s; }}
            .article:hover {{ transform: translateX(5px); }}
            
            /* Style pour TES articles (Vert clair) */
            .mine {{ background: #f1f8e9; border-left: 5px solid #2e7d32; }}
            .mine a {{ color: #1b5e20; font-weight: bold; font-size: 1.1em; text-decoration:none; }}
            
            /* Style pour les articles AUTORITÉ (Blanc/Gris) */
            .external {{ background: #fff; border: 1px solid #e0e0e0; border-left: 5px solid #ccc; }}
            .external a {{ color: #555; font-weight: normal; text-decoration: none; }}
            
            .source-tag {{ font-size: 0.75em; text-transform: uppercase; margin-bottom: 5px; display:block; font-weight:bold; }}
            .tag-mine {{ color: #2e7d32; }}
            .tag-ext {{ color: #999; }}
        </style>
    </head>
    <body>
        <h1>🌍 Verde News - Agrégateur</h1>
        <p>Sélection du web et dossiers spéciaux ({datetime.datetime.now().strftime("%d/%m/%Y")})</p>
        
        <div id="news-container">
    """

    for item in final_list:
        css_class = "mine" if item['is_mine'] else "external"
        tag_class = "tag-mine" if item['is_mine'] else "tag-ext"
        source_label = "⭐ Dossier VerdeVoice" if item['is_mine'] else "📰 Ailleurs sur le web"
        
        html_content += f"""
            <div class="article {css_class}">
                <span class="source-tag {tag_class}">{source_label}</span>
                <a href="{item['link']}" target="_blank">{item['title']}</a>
            </div>
        """

    html_content += """
        </div>
        <div style="text-align:center; margin-top:50px; font-size:0.8em; color:#aaa; border-top:1px solid #eee; padding-top:20px;">
            Agrégateur automatique d'actualités écologiques.
        </div>
    </body>
    </html>
    """
    if not os.path.exists("public"):
        os.makedirs("public")
    # -------------------------------

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("2. Page HTML générée avec succès.")
    return True
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("2. Page HTML générée avec succès.")
    return True

def deploy_to_firebase():
    print("3. Envoi vers Firebase...")
    os.system("firebase deploy --only hosting")

if __name__ == "__main__":
    if generate_html():

        deploy_to_firebase()
