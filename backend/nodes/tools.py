from models import AccommodationSearchInput, Accommodation
from config import logger
from langchain_core.tools import tool
from typing import List
import requests
import os


RAPIDAPI_KEY = os.getenv("X_RAPIDAPI_KEY")
HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "booking-com15.p.rapidapi.com"
}

@tool
def accommodation_search(input: AccommodationSearchInput) -> List[Accommodation]:
    """
    Tool for searching hotels based on user preferences.
    It queries Booking.com APIs via RapidAPI to:
    1. Get the destination ID and type.
    2. Search for hotels in that destination.
    3. Retrieve detailed hotel information for each hotel.
    4. Parse the hotel detail into the Accommodation format.

    Parameters:
    - input (AccommodationSearchInput):
        This object holds all the necessary details for your hotel search.
        It includes prefs, itinerary, and destinations.
        - num_peoples: Number of travelers.
        - itinerary: Used for searching accommodation, based on the last activity's address of each daily itinerary.
            
    Returns:
    - List[Accommodation]: A list of structured accommodation results matching user preferences.
    """
    def getDestination(items):
        """
        From destination search results, find the one with 'dest' in its name,
        and extract its dest_id and dest_type.
        """
        for item in items:
            name = item.get("name", "")  
            if "dest" in name.lower():
                dest_id = item.get("dest_id")
                dest_type = item.get("type")
                return {"dest_id": dest_id, "dest_type": dest_type}
            
    def getHotelDetail(hotel_id):
        """
        Given a hotel_id, query the hotel detail endpoint and parse required fields
        into the Accommodation data structure. (Currently incomplete)
        """
        url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/getHotelDetails"
        querystring = {"hotel_id":"hotel_id","units":"metric","temperature_unit":"c","languagecode":"zh-tw","currency_code":"TWD"}
        response = requests.get(url, headers=HEADERS, params=querystring).json()

        name=response.get("hotel_name"),
        hotel_url=response.get("url"),
        address=response.get("address", "") + ", " + response.get("city", "") + ", " + response.get("country_trans", ""),
        price=float(response.get("composite_price_breakdown", {}).get("gross_amount_hotel_currency", {}).get("value", 0.0)),
        currency=response.get("composite_price_breakdown", {}).get("gross_amount_hotel_currency", {}).get("currency", "TWD"),
        review_score=float(response.get("review_score", 0.0)),
        review_count=int(response.get("review_nr", 0)),
        arrival_date=response.get("arrival_date"),
        departure_date=response.get("departure_date")


    logger.info("Use tool 'accomodation_searh'.")
    itinerary = input.itinerary
    destinations = []
    accommodations = []

    # 住宿地點: 每日行程的最後一個活動地點(區域)
    if not destinations and itinerary:
        destinations = [daily_itinerary.segments[-1].activities[-1].activity_location for daily_itinerary in itinerary.days]

    if not destinations:
        logger.error("No destination specified and no itinerary available to infer destinations.")
        raise ValueError("No destination specified and no itinerary available to infer destinations.")

    print("===Accommodation search with location===\n", destinations)
    get_destId_url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"
    search_hotels_url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"

    for dest in destinations:
        # 獲取dest_id和dest_type
        params = {"query": dest}
        dest_response = requests.get(get_destId_url, headers=HEADERS, params=params)
        items = dest_response.json().get("data", [])
        destination = getDestination(items)

        if not destination:
            continue

        # 搜尋符合條件的住宿
        params = {
            "dest_id": destination["dest_id"],
            "search_type": destination["dest_type"],
            "adults": input.num_peoples,
            "units": "metric",
            "temperature_unit": "c",
            "languagecode": "zh-tw",
            "currency_code": "TWD"
        }
        hotels_response = requests.get(search_hotels_url, headers=HEADERS, params=params)
        hotels = hotels_response.json().get("data", {}).get("hotels", [])
        accommodations = [getHotelDetail(hotel.get("hotel_id")) for hotel in hotels]

    logger.log("Accommodations:\n {accommodations}")

    return accommodations

ALL_TOOLS = [accommodation_search]
TOOL_MAP = {tool.name: tool for tool in ALL_TOOLS}


# Test
if __name__ == "__main__":
    import json

    data = '{"prefs":{"destination":"東京","dates":{"duration":"2 days 1 night","start_date":"2023-10-01","end_date":"2023-10-02"},"num_people":2,"budget":50000,"special_requests":null},"itinerary":{"travel_theme":"東京美食與文化探索","destination":"東京","dates":{"duration":"2 days 1 night","start_date":"2023-10-01","end_date":"2023-10-02"},"features":"融合東京的美食與文化，探索當地的特色料理與歷史景點。","days":[{"daily_theme":"東京街頭美食與文化探索","itinerary_location":"東京","date":"2023-10-01","segments":[{"time_slot":"Morning (09:00-12:00)","activities":[{"activity_name":"淺草寺","type":"Attraction","location":"淺草","description":"參觀東京最古老的寺廟，感受日本宗教文化的氛圍。","estimated_duration":"2 hours","notes":"建議早上前往以避開人潮。"}]},{"time_slot":"Afternoon (12:00-17:00)","activities":[{"activity_name":"築地市場","type":"Attraction","location":"築地","description":"參觀東京著名的築地市場，品嚐新鮮的海鮮和壽司。","estimated_duration":"2 hours","notes":"建議早上前往，市場熱鬧。"}]},{"time_slot":"Evening (17:00-22:00)","activities":[{"activity_name":"秋葉原電子城美食","type":"Restaurant","location":"秋葉原","description":"在秋葉原的電子城區尋找特色餐廳，享受日本拉麵或咖哩。","estimated_duration":"2 hours","notes":"多家餐廳可供選擇，可以試試不同風味。"}]}],"transportation":"主要搭乘地鐵和步行，方便遊覽。","accommodation":null},{"daily_theme":"東京高級美食與文化體驗","itinerary_location":"東京","date":"2023-10-02","segments":[{"time_slot":"Morning (09:00-12:00)","activities":[{"activity_name":"上野公園","type":"Attraction","location":"上野","description":"在上野公園散步，享受自然風光，並尋找公園內的小吃攤。","estimated_duration":"2 hours","notes":"適合拍照與放鬆的好地方。"}]},{"time_slot":"Afternoon (12:00-17:00)","activities":[{"activity_name":"銀座高級餐廳用餐","type":"Restaurant","location":"銀座","description":"在銀座的高級餐廳享用傳統的懷石料理，體驗日本的精緻飲食文化。","estimated_duration":"2 hours","notes":"建議提前預約，避免排隊。"}]},{"time_slot":"Evening (17:00-22:00)","activities":[{"activity_name":"東京塔夜景觀賞","type":"Attraction","location":"東京塔","description":"在東京塔觀賞城市夜景，並可以在塔內的餐廳享用晚餐。","estimated_duration":"2 hours","notes":"夜景非常美麗，適合拍照。"}]}],"transportation":"建議 使用地鐵和步行，方便快捷。","accommodation":null}]}}'
    data = json.loads(data)

    # # 從 TOOL_MAP 取工具
    tool = TOOL_MAP["accommodation_search"]
    result = tool.invoke(input=data)
    print(result)