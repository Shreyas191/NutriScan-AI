"""
Verify the shopping link generation logic.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import sys
from unittest.mock import MagicMock

# Mock pydantic
sys.modules["pydantic"] = MagicMock()
sys.modules["pydantic"].BaseModel = object

# Mock app.config
config_mock = MagicMock()
config_mock.settings.INSTACART_API_KEY = None
sys.modules["app.config"] = config_mock

# Mock app.models.biomarker
biomarker_mock = MagicMock()
class FoodRecommendation:
    def __init__(self, name, emoji, nutrient, amount, category):
        self.name = name
        self.emoji = emoji
        self.nutrient = nutrient
        self.amount = amount
        self.category = category
biomarker_mock.FoodRecommendation = FoodRecommendation
sys.modules["app.models.biomarker"] = biomarker_mock

# Mock httpx
sys.modules["httpx"] = MagicMock()

# Mock app.services.instacart
instacart_mock = MagicMock()
instacart_mock.create_shopping_list = MagicMock()
async def mock_create_list(recs, title=""):
    return {
        "cart_items": [],
        "shop_all_url": "https://instacart.com/mock-list",
        "api_used": True
    }
instacart_mock.create_shopping_list.side_effect = mock_create_list
instacart_mock.build_item_url = lambda name: f"https://instacart.com/s/{name}"
sys.modules["app.services.instacart"] = instacart_mock

# Now import shopping
from app.services import shopping

async def test_shopping_links():
    print("Testing shopping link generation...")
    
    recommendations = [
        FoodRecommendation(
            name="Spinach",
            emoji="🥬",
            nutrient="Iron",
            amount="1 cup",
            category="food"
        ),
        FoodRecommendation(
            name="Salmon",
            emoji="🐟",
            nutrient="Vitamin D",
            amount="3 oz",
            category="food"
        ),
        FoodRecommendation(
            name="Vitamin D3",
            emoji="💊",
            nutrient="Vitamin D",
            amount="1000 IU",
            category="supplement"
        )
    ]
    
    result = await shopping.create_shopping_links(recommendations)
    
    print("\nResult keys:", result.keys())
    assert "cart_items" in result
    assert "shopping_links" in result
    
    links = result["shopping_links"]
    print("\nShopping Links:")
    for market, url in links.items():
        print(f"  {market}: {url}")
        
    assert "instacart" in links
    assert "amazon" in links
    assert "walmart" in links
    
    print("\nCart Items:")
    for item in result["cart_items"]:
        print(f"  {item['name']}: {item['links']}")
        assert "instacart" in item["links"]
        assert "amazon" in item["links"]
        assert "walmart" in item["links"]
        
    print("\n✅ Verification successful!")

if __name__ == "__main__":
    asyncio.run(test_shopping_links())
