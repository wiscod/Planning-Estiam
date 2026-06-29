import asyncio
import os
import json
from datetime import datetime, timedelta
from icalendar import Calendar
import requests
from dotenv import load_dotenv

load_dotenv()

# Credentials from environment variables
ICS_URL = os.getenv("ICS_URL", "")

# Architecture paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "public", "data")


def get_current_and_next_week():
    """Retourne le numéro de la semaine en cours et la suivante."""
    today = datetime.now()
    week_num = today.isocalendar()[1]
    return week_num, week_num + 1


def parse_ics_file(ics_content: str) -> dict:
    """Parse le fichier ICS et retourne les cours groupés par semaine."""
    try:
        cal = Calendar.from_ical(ics_content)
        courses_by_week = {}

        for component in cal.walk():
            if component.name == "VEVENT":
                summary = str(component.get('summary', ''))
                dtstart = component.get('dtstart')

                if dtstart:
                    start_date = dtstart.dt
                    if hasattr(start_date, 'date'):
                        start_date = start_date.date()

                    week_num = start_date.isocalendar()[1]

                    if week_num not in courses_by_week:
                        courses_by_week[week_num] = []

                    # Corriger le décalage horaire (UTC+2)
                    time_obj = dtstart.dt
                    if hasattr(time_obj, 'hour'):
                        time_obj = time_obj + timedelta(hours=2)
                        time_str = time_obj.strftime('%H:%M')
                    else:
                        time_str = str(time_obj)

                    location_raw = str(component.get('location', '')).strip()
                    location = ""
                    if location_raw:
                        loc_lower = location_raw.lower()
                        if "distanciel" in loc_lower:
                            location = "Distanciel"
                        elif "salle" in loc_lower or "amphi" in loc_lower:
                            location = f"Presentiel - {location_raw}"
                        elif "présentiel" in loc_lower or "presentiel" in loc_lower:
                            location = "Presentiel"
                        else:
                            # If it's something else, just append it
                            location = f"Presentiel - {location_raw}"

                    if location:
                        time_str = f"{time_str} ({location})"

                    courses_by_week[week_num].append({
                        'date': start_date.strftime('%d %B').lower(),
                        'date_obj': start_date,
                        'time': time_str,
                        'matiere': summary.split(' - ')[0].strip() if ' - ' in summary else summary,
                    })

        # Trier par date
        for week in courses_by_week:
            courses_by_week[week].sort(key=lambda x: x['date_obj'])

        return courses_by_week
    except Exception as e:
        print(f"Erreur parsing ICS: {e}")
        return None


async def get_courses_from_ics():
    """Récupère les cours depuis le fichier ICS."""
    try:
        print("Téléchargement du fichier ICS...")
        response = requests.get(ICS_URL, timeout=10)
        response.raise_for_status()
        return parse_ics_file(response.text)
    except Exception as e:
        import traceback
        error_msg = f"Erreur ICS: {e}\n{traceback.format_exc()}"
        print(error_msg)
        os.makedirs(LOGS_DIR, exist_ok=True)
        with open(os.path.join(LOGS_DIR, "error_ics.txt"), "w") as f:
            f.write(error_msg)
        return None


def format_planning(courses_by_week: dict, week_current: int, week_next: int) -> str:
    """Formate le planning sur 2 semaines."""
    jours_map = {
        "13 april": "LUNDI 13 AVRIL",
        "14 april": "MARDI 14 AVRIL",
        "15 april": "MERCREDI 15 AVRIL",
        "16 april": "JEUDI 16 AVRIL",
        "17 april": "VENDREDI 17 AVRIL",
        "20 april": "LUNDI 20 AVRIL",
        "21 april": "MARDI 21 AVRIL",
        "22 april": "MERCREDI 22 AVRIL",
        "23 april": "JEUDI 23 AVRIL",
        "24 april": "VENDREDI 24 AVRIL",
        "27 april": "LUNDI 27 AVRIL",
        "28 april": "MARDI 28 AVRIL",
        "29 april": "MERCREDI 29 AVRIL",
        "30 april": "JEUDI 30 AVRIL",
        "1 may": "VENDREDI 1 MAI",
        "2 may": "SAMEDI 2 MAI",
        "3 may": "DIMANCHE 3 MAI",
        "4 may": "LUNDI 4 MAI",
        "5 may": "MARDI 5 MAI",
    }

    message = "📅 *VOTRE PLANNING*\n\n"

    for week_num in [week_current, week_next]:
        cours_list = courses_by_week.get(week_num, [])
        if not cours_list:
            continue

        message += f"*SEMAINE {week_num}*\n\n"

        jour_courant = None
        for i, cours in enumerate(cours_list):
            date_normalized = cours['date'].lower()

            if date_normalized != jour_courant:
                jour_courant = date_normalized
                jour_complet = jours_map.get(date_normalized, date_normalized.upper())
                message += f"✨ {jour_complet}\n"
                message += "━━━━━━━━━━━━━━\n"

            message += f"- {cours['time']} : *{cours['matiere']}*\n"

            if i < len(cours_list) - 1 and cours_list[i + 1]['date'].lower() != jour_courant:
                message += "ㅤ\n"

        message += "\n"

    return message


def save_planning_json(courses_by_week: dict, week_current: int, week_next: int) -> bool:
    """Sauvegarde le planning en fichier JSON pour le widget iPhone."""
    try:
        planning_data = {
            "timestamp": datetime.now().isoformat(),
            "weeks": {}
        }

        for week_num in [week_current, week_next]:
            cours_list = courses_by_week.get(week_num, [])
            if not cours_list:
                continue

            planning_data["weeks"][str(week_num)] = {
                "semaine": week_num,
                "courses": [
                    {
                        "date": course["date"],
                        "time": course["time"],
                        "matiere": course["matiere"]
                    }
                    for course in cours_list
                ]
            }

        # Sauvegarder dans /public/data pour la vue web
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, "planning.json"), "w", encoding="utf-8") as f:
            json.dump(planning_data, f, ensure_ascii=False, indent=2)

        print("✅ Planning sauvegardé en JSON")
        return True
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde JSON: {e}")
        return False


async def main():
    print("=" * 60)
    print(f"Execution à {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)

    week_current, week_next = get_current_and_next_week()
    print(f"\nSemaine en cours: {week_current}, Semaine suivante: {week_next}")

    print("\n1️⃣ Récupération du fichier ICS...")
    courses_by_week = await get_courses_from_ics()

    if courses_by_week is None:
        print("❌ Impossible de récupérer les cours")
        return

    print("✏️ Formatage du message...")
    message = format_planning(courses_by_week, week_current, week_next)

    print("\n📤 Message formaté :\n")
    print(message)
    print("=" * 60)

    # Sauvegarder en JSON pour le widget iPhone et la vue web
    save_planning_json(courses_by_week, week_current, week_next)


if __name__ == "__main__":
    asyncio.run(main())
