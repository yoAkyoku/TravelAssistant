from pydantic import BaseModel, Field
from typing import TypedDict, Optional, List, Annotated, Literal
from langgraph.graph.message import add_messages, BaseMessage
from datetime import date, datetime

### Agent States/Models
class UserPreferences(BaseModel):
    destination: Optional[str] = Field(description="Travel destination")
    departure_location: Optional[str] = Field(description="Travel departure point.")
    num_peoples: Optional[int] = Field(1, description="Number of Travelers.", ge=1)
    departure_date: Optional[date] = Field(None, description="Start date of the trip (YYYY-MM-DD format)")
    return_date: Optional[date] = Field(None, description="End date of the trip (YYYY-MM-DD format)")
    duration: Optional[str] = Field(None, description="Travel duration in a string format, e.g., 'n days n-1 nights'")
    interests: Optional[List[str]] = Field(default_factory=list, description="User interests for activities")

class UserPreferencesState(BaseModel):
    prefs: UserPreferences = Field(UserPreferences, description="User preferences")
    preference_history: Optional[str] = Field("", description="User input history (Preference collection phase).")
    complete: bool = Field(False, description="Preferences are complete/no missing")

class CollectPreference(BaseModel):
    preferences: UserPreferences
    updated_field: str = Field(description="Updated field")

class Activity(BaseModel):
    """Detailed information for a single activity."""
    activity_name: Optional[str] = Field("", description="The specific name of the attraction, restaurant, experience, or activity.")
    type: Optional[str] = Field("",description="The category of the activity, e.g., 'Attraction', 'Restaurant', 'Shopping', 'Experience', 'Transportation'.")
    activity_location: Optional[str] = Field("", description="The specific place where the activity happens, e.g., 'Tokyo Tower', 'Asakusa'.")
    description: Optional[str] = Field("", description="A brief introduction or suggestion for the activity, e.g., 'Visit an ancient temple to feel the historical atmosphere'.")
    estimated_duration: Optional[str] = Field("", description="The estimated time required for this activity, e.g., '2 hours', '1.5 hours'.")
    notes: Optional[str] = Field("", description="Additional notes for this specific activity, suchs as: 'Reservation recommended', 'Suggest wearing comfortable shoes'.")

class TimeSegment(BaseModel):
    """Activity arrangements for a time segment within a day."""
    time_slot: Optional[str] = Field("", description="Defines the specific time slot for the day, suggested format: 'Morning (09:00-12:00)', 'Afternoon (13:00-17:00)', 'Evening (18:00-22:00)'.")
    activities: List[Activity] = Field(default_factory=list, description="All specific activities within this time segment.")

class Accommodation(BaseModel):
    hotel_id: Optional[int] = Field("", description="Unique identifier of the hotel.")
    name: Optional[str] = Field("", description="The official name of the hotel.")
    url: Optional[str] = Field("", description="Direct link to the hotel page on Booking.com.")
    address: Optional[str] = Field("", description="Full address of the hotel.")
    price: Optional[float] = Field("", description="Price per night in the specified currency.")
    currency: Optional[str] = Field("", description="Currency code for the price (e.g., 'USD', 'INR').")
    review_score: Optional[float] = Field("", description="Average customer review score for the hotel.")
    review_count: Optional[int] = Field("", description="Total number of customer reviews.")
    arrival_date: Optional[date] = Field(None, description="Check-in date in YYYY-MM-DD format.")
    departure_date: Optional[date] = Field(None, description="Check-out date in YYYY-MM-DD format.")

class DailyItinerary(BaseModel):
    """Detailed planning for a single day's itinerary."""
    daily_theme: Optional[str] = Field("", description="A concise summary of the day's core activities or experience theme, e.g., 'Cultural Exploration Day', 'Nature Scenic Tour', 'Urban Shopping Spree'.")
    itinerary_location: Optional[str] = Field("", description="Refers to the city, region, or main location where the day's primary activities take place.")
    day: Optional[date] = Field(None, description="The specific date for this itinerary, suggested format: YYYY-MM-DD.")
    segments: List[TimeSegment] = Field(default_factory=list, description="Contains detailed activity arrangements for different time segments within the day.")
    transportation: Optional[str] = Field("", description="Overall transportation suggestions for getting between activity locations during the day, e.g., 'Mainly rely on subway and walking, consider taxi for some sections.'")
    accommodation: Optional[Accommodation] = Field(None, description="Accommodation arrangements for the night.")

class ItineraryPlanning(BaseModel):
    """
    Travel Itinerary Planning (Overall itinerary summary and daily itinerary details)
    """
    # Overall itinerary summary
    travel_theme: Optional[str] = Field("",description="Travel theme (e.g., 'Kenting Sunny Beaches Chill Out' or 'Kyoto Ancient City Cultural Deep Dive').")
    description: Optional[str] = Field("",description="Trip plan description.")
    departure_location: Optional[str] = Field("",description="Travel departure point.")
    destination: Optional[str] = Field("",description="Country/City/Region (e.g., Japan Tokyo -> Sapporo -> Hokkaido).")
    num_peoples: Optional[int] = Field(1, description="Number of Travelers.", ge=1)
    duration: Optional[str] = Field("", description="Travel duration in a string format, e.g., 'n 天 n-1 夜'")
    start_date: Optional[date] = Field(None, description="Start date of the trip (YYYY-MM-DD format)")
    end_date: Optional[date] = Field(None, description="End date of the trip (YYYY-MM-DD format)")
    features: Optional[str] = Field("",description="Summarize the most appealing aspects of the trip in one sentence or a few keywords.")

    # Daily itinerary details
    days: List[DailyItinerary] = Field(default_factory=list,description="A list of detailed daily itinerary plans.")

    class Config:
        orm_mode = True

class PlanningState(BaseModel):
    """
    Represents the state of the planning process in the graph.
    """
    planning_options: List[ItineraryPlanning] = Field(default_factory=list, description="List of planning options generated by the agent")
    current_itinerary: ItineraryPlanning = Field(default_factory=dict, description="Current itinerary")

class AccommodationSearchInput(BaseModel):
    """
    Input schema for the accommodation_search tool.
    This model defines all the necessary parameters for the accommodation search tool
    to find suitable hotels based on user preferences and itinerary details.
    """
    num_peoples: int = Field(1, description="Number of Travelers.", ge=1)
    itinerary: Optional[ItineraryPlanning] = Field(default=None, description="Used for searching accommodation, based on the last activity's address of each daily itinerary.")

class TravelAssistantState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    planning: Optional[PlanningState]
    user_preferences: Optional[UserPreferencesState]
    intent: Optional[str] = Literal["chat", "plan_trip", "find_hotel", "modify_plan"]

### API Request/Respose Models
class ChatRequest(BaseModel):
    user_id: str
    plan_id: str
    message: str

class PlanResponse(ItineraryPlanning):
    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

class PlanUpdate(ItineraryPlanning):
    status: str