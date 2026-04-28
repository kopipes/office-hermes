from main import _classify_query, _extract_entities


def test_extract_entities_project_from_status_query():
    entities = _extract_entities("What is the latest status of CPP?")
    assert entities["project"] == "CPP"


def test_classify_report_query():
    route = _classify_query("report weekly", {"project": None, "client": None, "vendor": None, "business_unit": None})
    assert route["intent"] == "report_generation"
    assert route["tool"] == "generate_report"


def test_classify_wiki_query():
    route = _classify_query("/wiki procurement SOP", {"project": None, "client": None, "vendor": None, "business_unit": None})
    assert route["intent"] == "wiki_truth"
    assert route["tool"] == "search_wiki"
