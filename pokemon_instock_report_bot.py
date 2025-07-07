import os
import requests
from bs4 import BeautifulSoup

# We’ll read either a dedicated secret or fall back to your existing one:
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL_IN_STOCK") \
                   or os.environ.get("DISCORD_WEBHOOK_URL")

RETAILERS = [
    {
        "name": "Walmart",
        "url": "https://www.walmart.com/browse/collectibles/pokemon-cards/5967908_9807313_4252400?facet=retailer_type%3AWalmart",
        "product_container_selector": "div[data-item-id]",
        "product_name_selector": "span[data-automation-id='product-title']",
        "out_of_stock_selector": "div.gray"
    },
    {
        "name": "Best Buy",
        "url": "https://www.bestbuy.com/site/searchpage.jsp?browsedCategory=pcmcat1604992984556&id=pcat17071&qp=brandcharacter_facet%3DFranchise%7EPok%C3%A9mon&st=categoryid%24pcmcat1604992984556",
        "product_container_selector": "li.sku-item",
        "product_name_selector": "h4.sku-title > a",
        "out_of_stock_selector": "button[data-button-state='SOLD_OUT']"
    },
    {
        "name": "Target",
        "url": "https://www.target.com/c/collectible-trading-cards-hobby-collectibles-toys/pokemon/-/N-27p31Z569t0",
        "product_container_selector": "div.styles__StyledCol-sc-fw90uk-0.dOpyUp > div.styles__StyledCard-sc-1nkv38g-0.jGeGZz",
        "product_name_selector": "a[data-test='product-title']",
        "out_of_stock_selector": "div[data-test='soldOutLabel']"
    },
    {
        "name": "Pokemon Center",
        "url": "https://www.pokemoncenter.com/category/tcg-cards",
        "product_container_selector": "li.product-tile",
        "product_name_selector": "a.name",
        "out_of_stock_selector": "span.sold-out"
    }
]

def send_discord_report(report):
    if not DISCORD_WEBHOOK_URL:
        print("No webhook URL set")
        return

    # build a single embed
    embed = {
        "title": "📦 Pokémon TCG Current In-Stock Report",
        "description": "Here’s what’s in stock right now:",
        "color": 5814783,
        "fields": []
    }

    for retailer, items in report.items():
        if items:
            embed["fields"].append({
                "name": f"{retailer}",
                "value": "\n".join(f"- {item}" for item in items),
                "inline": False
            })

    if not embed["fields"]:
        embed["description"] = "🚫 No Pokémon cards currently in stock at any retailer."

    payload = {"embeds": [embed]}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print("Failed to send report to Discord:", e)

def scrape_and_build_report():
    report = {}
    headers = {'User-Agent': 'Mozilla/5.0'}
    for r in RETAILERS:
        print(f"Checking {r['name']}...", end=" ")
        try:
            resp = requests.get(r['url'], headers=headers, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")
            products = soup.select(r["product_container_selector"])
            in_stock = []
            for prod in products:
                name_el = prod.select_one(r["product_name_selector"])
                if not name_el: 
                    continue
                name = name_el.text.strip()
                if not prod.select_one(r["out_of_stock_selector"]):
                    in_stock.append(name)
            report[r["name"]] = in_stock
            print(f"found {len(in_stock)} in-stock")
        except Exception as e:
            print("ERROR:", e)
            report[r["name"]] = []
    return report

if __name__ == "__main__":
    report = scrape_and_build_report()
    send_discord_report(report)
