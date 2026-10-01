import os
from typing import Any, Mapping, Sequence
from dotenv import load_dotenv
from langchain_core.tools import Tool
from supabase import Client, create_client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables.")

supabase: Client = create_client(supabase_url, supabase_key)  # pyright: ignore[reportArgumentType]


def format_services_for_context(services: Sequence[Mapping[str, Any]]) -> str:  
    """Transforms nested relational data into a single formatted text block for LLM prompt injection."""
    blocks = []

    for service in services:
        features = [f.get("name") for f in service.get("service_feature", []) if f.get("name")]
        features_str = ", ".join(features) if features else "None"

        extras = []
        for extra in service.get("service_extra", []):
            label = extra.get("label")
            price = extra.get("price_per_unit")
            extras.append(f"{label} (${price}/unit)" if price else f"{label}")
        extras_str = "; ".join(extras) if extras else "None"

        pricing_options = []
        for price_opt in service.get("pricing_option", []):
            opt_str = f"{price_opt.get('label')} (${price_opt.get('price')})"
            sub_options = [
                f"{sub.get('label')} (${sub.get('price')})" 
                for sub in price_opt.get("sub_pricing_option", [])
            ]
            if sub_options:
                opt_str += f" [Sub-options: {', '.join(sub_options)}]"
            pricing_options.append(opt_str)
        pricing_str = "; ".join(pricing_options) if pricing_options else "None"

        text_payload = (
            f"Service Name: {service.get('name')}\n"
            f"Status: {service.get('status')}\n"
            f"Description: {service.get('description')}\n"
            f"Features: {features_str}\n"
            f"Add-ons/Extras: {extras_str}\n"
            f"Pricing Structure: {pricing_str}"
        )

        blocks.append(text_payload)

    # Returns one formatted text payload for the LLM
    return "\n\n---\n\n".join(blocks)


def fetch_available_services(query: str = "") -> str:
    """Fetch available services with their prices and format as text context."""
    response = supabase.table("service").select(
        "id, name, description, status, "
        "service_feature(name), "
        "service_extra(label, input_type, min_value, max_value, default_value, price_per_unit), "
        "pricing_option(label, price, sub_pricing_option(label, price, original_price))"
    ).execute()
    
    if not response.data:
        return "No active services found."

    return format_services_for_context(response.data) # pyright: ignore[reportArgumentType]


get_data_format_tool = Tool(
    name="get_data_info",
    func=fetch_available_services,
    description="Fetch data up-to-date about the available services with all their pricing and offers"
)