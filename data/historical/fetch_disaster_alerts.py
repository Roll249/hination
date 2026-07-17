#!/usr/bin/env python3
"""
GDACS Disaster Alert Fetcher for Vietnam

This script fetches real-time disaster alerts from GDACS (Global Disaster Alert 
and Coordination System) for Vietnam and the Southeast Asia region.

API Documentation: https://www.gdacs.org/Documents/2025/GDACS_API_quickstart_v2.pdf

Usage:
    python fetch_disaster_alerts.py
    python fetch_disaster_alerts.py --country Vietnam --days 90
    python fetch_disaster_alerts.py --event-type FL --output data/disasters/gdacs_floods.json
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    import requests
except ImportError:
    print("Error: 'requests' library required. Install with: pip install requests")
    sys.exit(1)


# GDACS API Configuration
BASE_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"
DETAIL_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventdata"

# Event types
EVENT_TYPES = {
    "FL": "Flood",
    "TC": "Tropical Cyclone",
    "EQ": "Earthquake",
    "DR": "Drought",
    "VO": "Volcano",
    "TS": "Tsunami",
}

# Vietnam-related keywords for filtering
VIETNAM_KEYWORDS = [
    "vietnam", "viet nam", "hanoi", "ho chi minh", 
    "mekong", "red river", "south china sea",
    "dien bien", "sa pa", "da nang", "hue",
    "vincity", "vung tau", "cantho", "can tho"
]

# Southeast Asia countries
SEA_COUNTRIES = ["Vietnam", "Laos", "Cambodia", "Thailand", "Myanmar", "China", "Philippines"]


class GDACSFetcher:
    """Fetch and process GDACS disaster alerts."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "HINATION-Disaster-Dashboard/1.0"
        })
    
    def fetch_events(
        self,
        event_types: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        alert_levels: Optional[List[str]] = None,
        country: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch events from GDACS API.
        
        Args:
            event_types: List of event types (FL, TC, EQ, etc.)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            alert_levels: Alert levels (Green, Orange, Red)
            country: Filter by country name
        
        Returns:
            Dict containing features and metadata
        """
        params = {}
        
        # Event types
        if event_types:
            params["eventlist"] = ",".join(event_types)
        
        # Date range
        if from_date:
            params["fromDate"] = from_date
        if to_date:
            params["toDate"] = to_date
        
        # Alert levels (semicolon-separated)
        if alert_levels:
            params["alertlevel"] = ";".join(alert_levels)
        
        print(f"Fetching GDACS events...")
        print(f"  URL: {BASE_URL}")
        print(f"  Params: {params}")
        
        try:
            response = self.session.get(BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Add metadata
            data["fetched_at"] = datetime.now().isoformat()
            data["query_params"] = params
            
            # Filter by country if specified
            if country:
                data["features"] = [
                    f for f in data.get("features", [])
                    if country.lower() in str(f.get("properties", {}).get("country", "")).lower()
                    or country.lower() in str(f.get("properties", {}).get("name", "")).lower()
                ]
                data["filtered_by_country"] = country
                data["total_filtered"] = len(data["features"])
            
            print(f"  Found {len(data.get('features', []))} events")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching GDACS data: {e}")
            return {"error": str(e), "features": []}
    
    def fetch_event_details(self, event_type: str, event_id: int) -> Dict[str, Any]:
        """Fetch detailed information for a specific event."""
        params = {
            "eventtype": event_type,
            "eventid": str(event_id)
        }
        
        try:
            response = self.session.get(DETAIL_URL, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching event details: {e}")
            return {"error": str(e)}
    
    def filter_vietnam_events(self, features: List[Dict]) -> List[Dict]:
        """Filter events specifically related to Vietnam."""
        vietnam_events = []
        
        for feature in features:
            props = feature.get("properties", {})
            name = props.get("name", "").lower()
            country = props.get("country", "").lower()
            
            # Check for Vietnam in name or country
            if "vietnam" in name or "vietnam" in country:
                vietnam_events.append(feature)
                continue
            
            # Check for SEA countries (may affect Vietnam)
            if country in [c.lower() for c in SEA_COUNTRIES]:
                # Check coordinates (rough bounds for Vietnam region)
                geom = feature.get("geometry", {})
                coords = geom.get("coordinates", [])
                if len(coords) >= 2:
                    lon, lat = coords[0], coords[1]
                    # Vietnam roughly: 8°N-24°N, 102°E-110°E
                    if 8 <= lat <= 24 and 102 <= lon <= 110:
                        vietnam_events.append(feature)
        
        return vietnam_events
    
    def format_for_dashboard(self, features: List[Dict]) -> List[Dict]:
        """Format GDACS events for dashboard display."""
        formatted = []
        
        for feature in features:
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            
            formatted_event = {
                "id": props.get("eventid"),
                "type": EVENT_TYPES.get(props.get("eventtype"), props.get("eventtype")),
                "type_code": props.get("eventtype"),
                "name": props.get("name"),
                "description": props.get("description"),
                "country": props.get("country"),
                "alert_level": props.get("alertlevel"),
                "alert_score": props.get("alertscore"),
                "from_date": props.get("fromdate"),
                "to_date": props.get("todate"),
                "glide": props.get("glide"),
                "coordinates": geom.get("coordinates"),
                "severity": props.get("severitydata", {}).get("severity"),
                "severity_unit": props.get("severitydata", {}).get("severityunit"),
                "urls": {
                    "report": props.get("url", {}).get("report"),
                    "details": props.get("url", {}).get("details"),
                }
            }
            formatted.append(formatted_event)
        
        return formatted


def main():
    parser = argparse.ArgumentParser(description="Fetch GDACS disaster alerts")
    parser.add_argument("--country", default="Vietnam", help="Country filter")
    parser.add_argument("--days", type=int, default=180, help="Days to look back")
    parser.add_argument("--event-type", action="append", help="Event types (can repeat)")
    parser.add_argument("--alert-level", action="append", help="Alert levels")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--detailed", action="store_true", help="Fetch detailed info for each event")
    
    args = parser.parse_args()
    
    fetcher = GDACSFetcher()
    
    # Calculate date range
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    
    # Fetch events
    event_types = args.event_type if args.event_type else list(EVENT_TYPES.keys())
    alert_levels = args.alert_level if args.alert_level else ["Green", "Orange", "Red"]
    
    result = fetcher.fetch_events(
        event_types=event_types,
        from_date=from_date,
        to_date=to_date,
        alert_levels=alert_levels,
    )
    
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    
    # Filter Vietnam events
    all_features = result.get("features", [])
    vietnam_events = fetcher.filter_vietnam_events(all_features)
    
    # Format for dashboard
    formatted = fetcher.format_for_dashboard(vietnam_events)
    
    # Output
    output_data = {
        "fetched_at": result["fetched_at"],
        "query": {
            "country": args.country,
            "from_date": from_date,
            "to_date": to_date,
            "event_types": event_types,
            "alert_levels": alert_levels,
        },
        "total_events": len(formatted),
        "events": formatted,
    }
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"  Total GDACS events: {len(all_features)}")
    print(f"  Vietnam-related events: {len(vietnam_events)}")
    
    if formatted:
        print(f"\n🌍 Recent Vietnam events:")
        for event in formatted[:5]:
            print(f"  [{event['alert_level']}] {event['type']}: {event['name']}")
            print(f"    Period: {event['from_date']} to {event['to_date']}")
    
    # Save or print
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved to: {output_path}")
    else:
        print("\n" + json.dumps(output_data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
