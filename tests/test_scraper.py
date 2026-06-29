"""Tests unitaires pour la logique de parsing ICS du scraper."""

from scraper import get_current_and_next_week, parse_ics_file

ICS_SAMPLE = """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
BEGIN:VEVENT
DTSTART:20260707T073000Z
DTEND:20260707T110000Z
SUMMARY:Info System Management - Groupe A
LOCATION:Distanciel
END:VEVENT
BEGIN:VEVENT
DTSTART:20260708T120000Z
DTEND:20260708T150000Z
SUMMARY:DevOps - Groupe B
LOCATION:Salle G (Victor HUGO)
END:VEVENT
END:VCALENDAR"""


def test_semaine_courante_et_suivante_sont_consecutives():
    current, nxt = get_current_and_next_week()
    assert nxt == current + 1


def test_numero_semaine_dans_plage_valide():
    current, _ = get_current_and_next_week()
    assert 1 <= current <= 53


def test_parse_ics_retourne_un_dictionnaire():
    result = parse_ics_file(ICS_SAMPLE)
    assert isinstance(result, dict)
    assert len(result) >= 1


def test_parse_ics_extrait_le_bon_nombre_de_cours():
    result = parse_ics_file(ICS_SAMPLE)
    all_courses = [c for week in result.values() for c in week]
    assert len(all_courses) == 2


def test_parse_ics_chaque_cours_a_les_champs_requis():
    result = parse_ics_file(ICS_SAMPLE)
    all_courses = [c for week in result.values() for c in week]
    for course in all_courses:
        assert "date" in course
        assert "time" in course
        assert "matiere" in course


def test_parse_ics_location_distanciel_dans_time():
    result = parse_ics_file(ICS_SAMPLE)
    all_courses = [c for week in result.values() for c in week]
    distanciel = [c for c in all_courses if "Distanciel" in c["time"]]
    assert len(distanciel) >= 1


def test_parse_ics_location_presentiel_dans_time():
    result = parse_ics_file(ICS_SAMPLE)
    all_courses = [c for week in result.values() for c in week]
    presentiel = [c for c in all_courses if "Presentiel" in c["time"]]
    assert len(presentiel) >= 1


def test_parse_ics_contenu_invalide_retourne_none():
    result = parse_ics_file("CONTENU NON ICS")
    assert result is None


def test_format_planning():
    from scraper import format_planning
    sample_courses = {
        27: [{'date': '13 april', 'time': '09:30', 'matiere': 'Maths'}],
        28: [{'date': '20 april', 'time': '14:00', 'matiere': 'DevOps'}]
    }
    result = format_planning(sample_courses, 27, 28)
    assert "VOTRE PLANNING" in result
    assert "SEMAINE 27" in result
    assert "Maths" in result
    assert "SEMAINE 28" in result
    assert "DevOps" in result


def test_save_planning_json(tmp_path):
    from scraper import save_planning_json
    import scraper
    # Override DATA_DIR temporarily for the test
    original_data_dir = scraper.DATA_DIR
    try:
        scraper.DATA_DIR = str(tmp_path)
        sample_courses = {
            27: [{'date': '13 april', 'time': '09:30', 'matiere': 'Maths'}],
        }
        success = save_planning_json(sample_courses, 27, 28)
        assert success is True
        
        import os
        import json
        json_file = os.path.join(str(tmp_path), "planning.json")
        assert os.path.exists(json_file)
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "weeks" in data
            assert "27" in data["weeks"]
            assert data["weeks"]["27"]["courses"][0]["matiere"] == "Maths"
    finally:
        scraper.DATA_DIR = original_data_dir
