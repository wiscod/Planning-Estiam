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
