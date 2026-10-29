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
    def get_driver_standings(year: int = 2024, round_number: int = None):
        try:
            from src.jolpica_client import JolpicaF1Client
            client = JolpicaF1Client()
            standings = client.get_driver_standings(year, round_number)
            formatted = []
            for item in standings:
                driver = item.get("Driver", {})
                constructors = item.get("Constructors", [])
                team_name = constructors[0].get("name", "Unknown") if constructors else "Unknown"
                formatted.append({
                    "position": int(item.get("position", 0)),
                    "points": float(item.get("points", 0.0)),
                    "wins": int(item.get("wins", 0)),
                    "driver_id": driver.get("driverId", ""),
                    "driver_code": driver.get("code", driver.get("driverId", "")[:3].upper()),
                    "driver_name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                    "permanent_number": driver.get("permanentNumber", ""),
                    "team_name": team_name,
                    "nationality": driver.get("nationality", "")
                })
            return {
                "success": True,
                "year": year,
                "season": year,
                "round_number": round_number,
                "standings": formatted
            }
        except Exception as e:
            return {"success": False, "error": str(e), "standings": []}

    @staticmethod
    def get_constructor_standings(year: int = 2024, round_number: int = None):
        try:
            from src.jolpica_client import JolpicaF1Client
            client = JolpicaF1Client()
            standings = client.get_constructor_standings(year, round_number)
            formatted = []
            for item in standings:
                constructor = item.get("Constructor", {})
                formatted.append({
                    "position": int(item.get("position", 0)),
                    "points": float(item.get("points", 0.0)),
                    "wins": int(item.get("wins", 0)),
                    "constructor_id": constructor.get("constructorId", ""),
                    "constructor_name": constructor.get("name", ""),
                    "team_name": constructor.get("name", ""),
                    "nationality": constructor.get("nationality", "")
                })
            return {
                "success": True,
                "year": year,
                "season": year,
                "round_number": round_number,
                "standings": formatted
            }
        except Exception as e:
            return {"success": False, "error": str(e), "standings": []}

    @staticmethod
    def get_drivers(session_id: str):
        # We can use a session to get the driver list and their teams
        try:
            from src.session_utils import parse_session_id
            year, event, session_type = parse_session_id(session_id)

            from src.data_providers import get_provider
            provider = get_provider()
            data = provider.fetch_session_data(year, event, session_type)
            results = data.get("results") if data.get("success") else None

            # Fallback for active/future or live sessions where FastF1 has no archive yet
            if results is None or results.empty:
                try:
                    from src.jolpica_client import JolpicaF1Client
                    j_client = JolpicaF1Client()
                    standings = j_client.get_driver_standings(year)
                    if not standings and year > 2024:
                        standings = j_client.get_driver_standings(2026) or j_client.get_driver_standings(2024)
                    
                    if standings:
                        drivers = []
                        for idx, item in enumerate(standings, 1):
                            d = item.get("Driver", {})
                            c = item.get("Constructors", [{}])[0]
                            team_name = c.get("name", "Formula 1 Team")
                            abbr = d.get("code") or d.get("driverId", "")[:3].upper()
                            num = d.get("permanentNumber") or str(idx)
                            full_name = f"{d.get('givenName', '')} {d.get('familyName', '')}".strip()
                            
                            team_color = "#E10600"
                            for k, v in {
                                "RED BULL": "#3671C6", "FERRARI": "#E8002D", "MCLAREN": "#FF8000",
                                "MERCEDES": "#27F4D2", "ASTON MARTIN": "#229971", "ALPINE": "#0093CC",
                                "WILLIAMS": "#64C4FF", "RB": "#6692FF", "RACING BULLS": "#6692FF",
                                "HAAS": "#B6BABD", "AUDI": "#52E252", "SAUBER": "#52E252", "CADILLAC": "#C92D4B"
                            }.items():
                                if k in team_name.upper():
                                    team_color = v
                                    break
                            
                            drivers.append({
                                "driver_number": str(num),
                                "broadcast_name": full_name or abbr,
                                "abbreviation": abbr,
                                "team_name": team_name,
                                "team_color": team_color,
                                "headshot_url": f"https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/{abbr}.png",
                                "position": idx,
                                "points": float(item.get("points", 0))
                            })
                        return {
                            "success": True,
                            "session_id": session_id,
                            "drivers": drivers
                        }
                except Exception as fallback_err:
                    pass

            if not data.get("success"):
                return {"success": False, "error": data.get("error", "Could not fetch session data.")}

            TEAM_COLORS = {
                "RED BULL RACING": "#3671C6", "RED BULL": "#3671C6",
                "FERRARI": "#E8002D", "SCUDERIA FERRARI": "#E8002D",
                "MCLAREN": "#FF8000",
                "MERCEDES": "#27F4D2",
                "ASTON MARTIN": "#229971",
                "ALPINE": "#0093CC",
                "WILLIAMS": "#64C4FF",
                "RB": "#6692FF", "RACING BULLS": "#6692FF", "ALPHATAURI": "#6692FF",
                "KICK SAUBER": "#52E252", "SAUBER": "#52E252", "ALFA ROMEO": "#C92D4B",
                "HAAS F1 TEAM": "#B6BABD", "HAAS": "#B6BABD"
            }

            DRIVER_HEADSHOTS = {
                "VER": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/maxver01.png.transform/2col/image.png",
                "PER": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/S/SERPER01_Sergio_Perez/serper01.png.transform/2col/image.png",
                "NOR": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LANNOR01_Lando_Norris/lannor01.png.transform/2col/image.png",
                "PIA": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/O/OSCPIA01_Oscar_Piastri/oscpia01.png.transform/2col/image.png",
                "LEC": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/C/CHALEC01_Charles_Leclerc/chalec01.png.transform/2col/image.png",
                "SAI": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/C/CARSAI01_Carlos_Sainz/carsai01.png.transform/2col/image.png",
                "HAM": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LEWHAM01_Lewis_Hamilton/lewham01.png.transform/2col/image.png",
                "RUS": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/G/GEORUS01_George_Russell/georus01.png.transform/2col/image.png",
                "ALO": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/F/FERALO01_Fernando_Alonso/feralo01.png.transform/2col/image.png",
                "STR": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LANSTR01_Lance_Stroll/lanstr01.png.transform/2col/image.png",
                "GAS": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/P/PIEGAS01_Pierre_Gasly/piegas01.png.transform/2col/image.png",
                "OCO": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/E/ESTOCO01_Esteban_Ocon/estoco01.png.transform/2col/image.png",
                "TSU": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/Y/YUKTSU01_Yuki_Tsunoda/yuktsu01.png.transform/2col/image.png",
                "RIC": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/D/DANRIC01_Daniel_Ricciardo/danric01.png.transform/2col/image.png",
                "LAW": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LIAMLA01_Liam_Lawson/liamla01.png.transform/2col/image.png",
                "HUL": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/N/NICHUL01_Nico_Hulkenberg/nichul01.png.transform/2col/image.png",
                "MAG": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/K/KEVMAG01_Kevin_Magnussen/kevmag01.png.transform/2col/image.png",
                "ALB": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/A/ALEALB01_Alexander_Albon/alealb01.png.transform/2col/image.png",
                "SAR": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LOGSAR01_Logan_Sargeant/logsar01.png.transform/2col/image.png",
                "COL": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/F/FRACOL01_Franco_Colapinto/fracol01.png.transform/2col/image.png",
                "BOT": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/V/VALBOT01_Valtteri_Bottas/valbot01.png.transform/2col/image.png",
                "ZHO": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/G/GUAZHO01_Guanyu_Zhou/guazho01.png.transform/2col/image.png",
                "BEA": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/O/OLIBEA01_Oliver_Bearman/olibea01.png.transform/2col/image.png",
                "ANT": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/K/KIMANT01_Kimi_Antonelli/kimant01.png.transform/2col/image.png",
                "DOO": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/J/JACDOO01_Jack_Doohan/jacdoo01.png.transform/2col/image.png",
                "BOR": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/G/GABBOR01_Gabriel_Bortoleto/gabbor01.png.transform/2col/image.png",
                "HAD": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/I/ISAHAD01_Isack_Hadjar/isahad01.png.transform/2col/image.png",
            }

            results = data.get("results")
            drivers = []
            if results is not None and not results.empty:
                for _, row in results.iterrows():
                    team = str(row.get('TeamName', 'Formula 1 Team'))
                    team_color = None
                    if 'TeamColor' in row and not pd.isna(row['TeamColor']) and row['TeamColor']:
                        col = str(row['TeamColor']).strip('#')
                        if col:
                            team_color = f"#{col}"
                    if not team_color:
                        for k, v in TEAM_COLORS.items():
                            if k in team.upper():
                                team_color = v
                                break
                    if not team_color:
                        team_color = "#E10600"

                    pos = row.get('Position', 20)
                    try:
                        pos_val = int(float(pos)) if pd.notna(pos) and str(pos).strip() != '' else 20
                    except (ValueError, TypeError):
                        pos_val = 20
                    abbr = str(row.get('Abbreviation', 'DRV')).upper()
                    headshot = DRIVER_HEADSHOTS.get(abbr, "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/driver_fallback.png")

                    drivers.append({
                        "driver_number": str(row.get('DriverNumber', '')),
                        "broadcast_name": str(row.get('FullName', row.get('BroadcastName', abbr))),
                        "abbreviation": abbr,
                        "team_name": team,
                        "team_color": team_color,
                        "headshot_url": headshot,
                        "position": pos_val,
                        "points": float(row.get('Points', 0)) if 'Points' in row and pd.notna(row['Points']) else 0.0
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
