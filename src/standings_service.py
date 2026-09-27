import fastf1
import pandas as pd

class StandingsService:
    @staticmethod
    def get_circuits(year: int):
        try:
            schedule = fastf1.get_event_schedule(year)
            # Remove testing sessions if any (EventFormat != 'testing')
            schedule = schedule[schedule['EventFormat'] != 'testing']

            circuits = []
            for _, row in schedule.iterrows():
                circuits.append({
                    "round": int(row['RoundNumber']),
                    "country": row['Country'],
                    "location": row['Location'],
                    "event_name": row['EventName'],
                    "event_date": row['EventDate'].strftime("%Y-%m-%d") if not pd.isna(row['EventDate']) else None,
                    "format": row['EventFormat']
                })

            return {
                "success": True,
                "year": year,
                "circuits": circuits
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_drivers(session_id: str):
        # We can use a session to get the driver list and their teams
        try:
            parts = session_id.split('-')
            year = int(parts[1]) if len(parts) > 1 else 2024
            event = parts[2] if len(parts) > 2 else "SPAIN"

            from src.data_providers import get_provider
            provider = get_provider()
            data = provider.fetch_session_data(year, event, 'R')
            if not data.get("success"):
                return {"success": False, "error": "Could not fetch session data."}

            session = data["raw_session"]
            results = session.results

            drivers = []
            if results is not None and not results.empty:
                for _, row in results.iterrows():
                    drivers.append({
                        "driver_number": row['DriverNumber'],
                        "broadcast_name": row['BroadcastName'],
                        "abbreviation": row['Abbreviation'],
                        "team_name": row['TeamName'],
                        "team_color": f"#{row['TeamColor']}" if not pd.isna(row['TeamColor']) else "#ffffff",
                        "position": row['Position'],
                        "points": row['Points']
                    })

            # Sort by position
            drivers = sorted(drivers, key=lambda x: x['position'] if not pd.isna(x['position']) else 99)

            return {
                "success": True,
                "session_id": session_id,
                "drivers": drivers
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
