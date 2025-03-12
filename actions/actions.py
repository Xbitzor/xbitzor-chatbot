import os
import re
import html
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests

# Load Shopify API credentials from environment variables
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")

# Validate credentials
if not SHOPIFY_ACCESS_TOKEN or not SHOPIFY_STORE_URL:
    raise ValueError("ERROR: Shopify API credentials are missing! Set SHOPIFY_ACCESS_TOKEN and SHOPIFY_STORE_URL in your environment.")

class ActionSearchShopify(Action):
    def name(self) -> Text:
        return "action_search_shopify"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        query = tracker.latest_message.get("text", "").strip()
        intent = tracker.latest_message.get("intent", {}).get("name", "")

        # Define API endpoints
        endpoints = {
            "legal_policies": "policies.json",
            "shipping_info": "shipping_zones.json",
            "payment_terms": "payment_terms.json",
            "price_rules": "price_rules.json",
            "check_inventory": "inventory_levels.json",
            "product_listings": "product_listings.json",
            "content_search": f"pages.json?title={query}"
        }

        if intent == "search_product":
            return self.search_product(dispatcher, query)

        if intent not in endpoints:
            dispatcher.utter_message(text="I'm sorry, I didn't understand that. Can you please rephrase?")
            return []

        api_url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/{endpoints[intent]}"
        headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}

        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200 and response.headers.get("Content-Type") == "application/json":
                data = response.json()
                return self.process_response(intent, data, dispatcher)
            else:
                dispatcher.utter_message(text="Sorry, I couldn't connect to Shopify right now.")
        except requests.exceptions.Timeout:
            dispatcher.utter_message(text="The request to Shopify timed out. Please try again later.")
        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text="There was an error connecting to Shopify.")
            print(f"ERROR: {str(e)}")

        return []

    def search_product(self, dispatcher: CollectingDispatcher, query: str) -> List[Dict[Text, Any]]:
        """Searches for a product by title."""
        api_url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/products.json"
        headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
        
        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "products" not in data:
                    dispatcher.utter_message(text="Error: No products found in the response.")
                    return []
                
                products = data.get("products", [])
                matching_products = [p for p in products if query.lower() in p.get("title", "").lower()]
                
                if matching_products:
                    product = matching_products[0]
                    dispatcher.utter_message(
                        text=f"I found this product: {product.get('title')}. Check it out here: {SHOPIFY_STORE_URL}/products/{product.get('handle')}"
                    )
                else:
                    dispatcher.utter_message(text="Sorry, I couldn't find any products matching your query.")
            else:
                dispatcher.utter_message(text="Error retrieving products from Shopify.")
        except requests.exceptions.Timeout:
            dispatcher.utter_message(text="The request to Shopify timed out. Please try again later.")
        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text="There was an error connecting to Shopify.")
            print(f"ERROR: {str(e)}")

        return []

    def process_response(self, intent: str, data: Dict, dispatcher: CollectingDispatcher) -> List[Dict[Text, Any]]:
        if intent == "legal_policies":
            policies = data.get("policies", {})
            if policies:
                for key, value in policies.items():
                    dispatcher.utter_message(text=f"{key.replace('_', ' ').title()}: {self.clean_text(value)}")
            else:
                dispatcher.utter_message(text="Sorry, I couldn't find any legal policies.")

        elif intent == "shipping_info":
            shipping_zones = data.get("shipping_zones", [])
            if shipping_zones:
                dispatcher.utter_message(text=f"Shipping Information: {shipping_zones[0].get('name', 'No shipping details available.')}")
            else:
                dispatcher.utter_message(text="Sorry, no shipping details found.")

        elif intent == "payment_terms":
            payment_terms = data.get("payment_terms", [])
            if payment_terms:
                dispatcher.utter_message(text=f"Payment Terms: {payment_terms[0].get('terms', 'No payment terms available.')}")
            else:
                dispatcher.utter_message(text="Sorry, no payment terms found.")

        elif intent == "price_rules":
            price_rules = data.get("price_rules", [])
            if price_rules:
                dispatcher.utter_message(text=f"Price Rule: {price_rules[0].get('title', 'No price rules available.')}")
            else:
                dispatcher.utter_message(text="Sorry, no price rules found.")

        elif intent == "check_inventory":
            inventory_levels = data.get("inventory_levels", [])
            if inventory_levels:
                dispatcher.utter_message(text=f"Inventory Level: {inventory_levels[0].get('available', 'No inventory data available.')}")
            else:
                dispatcher.utter_message(text="Sorry, no inventory data found.")

        elif intent == "content_search":
            pages = data.get("pages", [])
            if pages:
                dispatcher.utter_message(text=f"Page Found: {pages[0].get('title', 'No pages found.')}")
            else:
                dispatcher.utter_message(text="Sorry, no pages found.")

        return []

    def clean_text(self, text: str) -> str:
        """Cleans up text by removing HTML tags and decoding HTML entities."""
        clean_text = re.sub(r"<[^>]*>", "", text)
        clean_text = html.unescape(clean_text)
        clean_text = re.sub(r"\s+", " ", clean_text)
        return clean_text.strip()