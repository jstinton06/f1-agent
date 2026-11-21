def get_driver_info(driver_name: str) -> dict:
    """Return basic info about an F1 driver (fake data for testing)."""
    drivers = {
        "max verstappen": {"team": "red bull", "number": 3, "nationality": "dutch"},
        "isack hadjar": {"team": "red bull", "number": 10, "nationality": "french"},
        "kimi antonelli": {"team": "mercedes", "number": 12, "nationality": "italian"},
        "george russell": {"team": "mercedes", "number": 63, "nationality": "british"},
        "charles leclerc": {"team": "ferrari", "number": 16, "nationality": "monegasque"},
        "lewis hamilton": {"team": "ferrari", "number": 44, "nationality": "british"},
        "oscar piastri": {"team": "mclaren", "number": 81, "nationality": "australian"},
        "lando norris": {"team": "mclaren", "number": 1, "nationality": "british"}
    }

    key = driver_name.lower().strip()
    if key in drivers:
        return drivers[key]
    else:
        return {"error": f"No data found for '{driver_name}'"}