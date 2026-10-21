
import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

locations = {
    "Andhra Pradesh": {
        "Tirupati": ["Tirupati Main Road", "Renigunta Road", "Chandragiri Road", "Tiruchanur Road"],
        "Chittoor": ["Chittoor Bypass", "Palamaner Road", "Puttur Road"],
        "Guntur": ["Guntur Main Road", "NH 16", "Amaravati Road"],
        "Vijayawada": ["Benz Circle Road", "Eluru Road", "NH 65"],
        "Visakhapatnam": ["Beach Road", "Madhurawada Road", "NH 16"],
        "Nellore": ["Nellore Bypass", "Trunk Road"]
    },
    "Telangana": {
        "Hyderabad": ["Miyapur Road", "Kukatpally Main Road", "Outer Ring Road", "NH 65", "Gachibowli Road"],
        "Warangal": ["Warangal Main Road", "Hanamkonda Road"],
        "Khammam": ["Khammam Bypass", "Wyra Road"],
        "Nizamabad": ["Nizamabad Main Road", "NH 44"]
    },
    "Tamil Nadu": {
        "Chennai": ["Chennai Main Road", "OMR", "GST Road"],
        "Coimbatore": ["Coimbatore Bypass", "Avinashi Road"],
        "Madurai": ["Madurai Main Road", "NH 44"]
    },
    "Karnataka": {
        "Bengaluru": ["Bengaluru Main Road", "Outer Ring Road", "Mysore Road"],
        "Mysuru": ["Mysuru Road", "Bannur Road"],
        "Mangaluru": ["Mangaluru Main Road", "NH 66"]
    }
}

vehicles = ["Bike", "Car", "Bus", "Truck", "Auto"]
severities = ["Minor", "Major", "Fatal"]
weathers = ["Sunny", "Cloudy", "Rainy", "Foggy", "Windy"]

records = []
record_id = 1

for year in range(2011, 2027):
    start_date = datetime(year, 1, 1)
    next_year = datetime(year + 1, 1, 1)
    days_in_year = (next_year - start_date).days

    for _ in range(500):
        state = random.choice(list(locations.keys()))
        district = random.choice(list(locations[state].keys()))
        location = random.choice(locations[state][district])

        accident_date = start_date + timedelta(
            days=random.randint(0, days_in_year - 1)
        )

        accident_time = (
            datetime.min + timedelta(
                minutes=random.randint(0, 1439)
            )
        ).time()

        severity = random.choice(severities)

        if severity == "Minor":
            deaths = 0
            injuries = random.randint(1, 2)
        elif severity == "Major":
            deaths = random.randint(0, 1)
            injuries = random.randint(1, 5)
        else:
            deaths = random.randint(1, 3)
            injuries = random.randint(0, 4)

        records.append({
            "accident_id": record_id,
            "accident_date": accident_date.strftime("%Y-%m-%d"),
            "accident_time": accident_time.strftime("%H:%M:%S"),
            "state": state,
            "district": district,
            "location": location,
            "vehicle_type": random.choice(vehicles),
            "severity": severity,
            "deaths": deaths,
            "injuries": injuries,
            "weather": random.choice(weathers),
            "source": "Synthetic Data"
        })

        record_id += 1

df = pd.DataFrame(records)
df.to_csv("synthetic_accidents.csv", index=False)

print("Synthetic CSV created successfully!")
print("Total records:", len(df))

print("\nRecords per year:")
print(df.groupby(df["accident_date"].str[:4]).size())

print("\nRegions generated:")
print(df["state"].value_counts())

print("\nDifferent road locations:", df["location"].nunique())

print("\nWeather distribution:")
print(df["weather"].value_counts())

