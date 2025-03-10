import os
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests

SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")

print(f"DEBUG: SHOPIFY_ACCESS_TOKEN: {SHOPIFY_ACCESS_TOKEN}")
print(f"DEBUG: SHOPIFY_STORE_URL: {SHOPIFY_STORE_URL}")

if not SHOPIFY_ACCESS_TOKEN or not SHOPIFY_STORE_URL:
    print("ERROR: Shopify API credentials are missing!")

class ActionSearchShopify(Action):
    def name(self) -> Text:
        return "action_search_shopify"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        query = tracker.latest_message.get("text")
        intent = tracker.latest_message.get("intent", {}).get("name", "")

        if not SHOPIFY_ACCESS_TOKEN or not SHOPIFY_STORE_URL:
            dispatcher.utter_message(text="Shopify credentials are missing. Please check the configuration.")
            return []

        endpoints = {
            "search_product": f"products.json?title={query}",
            "legal_policies": "policies.json",
            "shipping_info": "shipping_zones.json",
            "payment_terms": "payment_terms.json",
            "price_rules": "price_rules.json",
            "check_inventory": "inventory_levels.json",
            "product_listings": "product_listings.json",
            "content_search": f"pages.json?title={query}"
        }

        if intent not in endpoints:
            dispatcher.utter_message(text="I'm sorry, I didn't understand that. Can you please rephrase?")
            return []

        api_url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/{endpoints[intent]}"
        headers = {
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
        }

        print(f"DEBUG: Shopify API request URL: {api_url}")

        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self.process_response(intent, data, dispatcher, SHOPIFY_STORE_URL)
            else:
                dispatcher.utter_message(text="Sorry, I couldn't connect to Shopify right now.")
        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text="There was an error connecting to Shopify.")
            print(f"ERROR: {str(e)}")
        
        return []

    def process_response(self, intent: str, data: Dict, dispatcher: CollectingDispatcher, store_url: str) -> List[Dict[Text, Any]]:
        """Processes API response based on the intent and sends a message."""
        if intent == "search_product":
            products = data.get("products", [])
            if products:
                product = products[0]
                dispatcher.utter_message(
                    text=f"I found this product: {product.get('title')}. Check it out here: {store_url}/products/{product.get('handle')}"
                )
            else:
                dispatcher.utter_message(text="Sorry, I couldn't find any products matching your query.")

        elif intent == "legal_policies":
            policies = data.get("policies", [])
            if policies:
                dispatcher.utter_message(text=f"Refund Policy: {policies.get('refund_policy', 'Not available')}")
            else:
                dispatcher.utter_message(text="Sorry, I couldn't find any legal policies.")

        return []
