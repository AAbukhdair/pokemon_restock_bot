import os
import requests
from bs4 import BeautifulSoup
import json

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
STATE_FILE = "last_seen.json"

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
        "url": "https://www.pokemoncenter.com/category/new-releases?category=S0105-0000-0000",
        "product_container_selector": "li.product-tile",
        "product_name_selector": "a.name",
        "out_of_stock_selector": "span.sold-out"
    }
]

def load_last_seen():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_last_seen(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def send_discord_message(msg):
    if not DISCORD_WEBHOOK_URL:
        print("No webhook URL set")
        return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})
    except Exception as e:
        print(f"Failed to send Discord message: {e}")

def main():
    print("Script started!")
    last_seen = load_last_seen()
    current_seen = {}
    found_new = False

    for r in RETAILERS:
        print(f"Checking {r['name']}...")
        in_stock = []
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(r['url'], headers=headers, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")
            products = soup.select(r["product_container_selector"])
            for prod in products:
                name_elem = prod.select_one(r["product_name_selector"])
                if name_elem:
                    name = name_elem.text.strip()
                    out_of_stock_elem = prod.select_one(r["out_of_stock_selector"])
                    currently_in_stock = out_of_stock_elem is None
                    in_stock.append((name, currently_in_stock))
        except Exception as e:
            print(f"Failed to scrape {r['name']}: {e}")
            continue

        prev = last_seen.get(r["name"], {})
        current_seen[r["name"]] = {}

        for name, stock in in_stock:
            current_seen[r["name"]][name] = stock
            was = prev.get(name, False)
            if stock and not was:
                send_discord_message(f"🎉 **Restock/New Item!** `{name}` now available at **{r['name']}**")
                found_new = True

    save_last_seen(current_seen)
    if not found_new:
        send_discord_message("No new items or restocks found at any retailer.")

if __name__ == "__main__":
    main()
