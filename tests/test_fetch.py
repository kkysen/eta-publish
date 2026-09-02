"""Tab selection, which is where a silent wrong-document bug would hide.

By default `documents.get` fills `body` from the first tab only,
so a report drafted in a later tab would parse cleanly and be wrong.
"""

from collections.abc import Sequence
from pathlib import Path

import pytest

from eta_publish.docs_json import JsonObject
from eta_publish.fetch import SCOPES, TabNotFound, parse_ref, select_tab

URL = (
    "https://docs.google.com/document/d/1U-M71SN5azsWSLAnp_1cPaPBj8YDHfb9Z8uoopVopBg"
    "/edit?tab=t.ul3yzv5xed4w"
)

DOC_ID = "1U-M71SN5azsWSLAnp_1cPaPBj8YDHfb9Z8uoopVopBg"


def _tab(tab_id: str, title: str, text: str, children: Sequence[JsonObject] = ()) -> JsonObject:
    return {
        "tabProperties": {"tabId": tab_id, "title": title},
        "documentTab": {"body": {"content": [{"marker": text}]}},
        "childTabs": list(children),
    }


MULTI_TAB = {
    "title": "SAS West Feasibility Response",
    "tabs": [
        _tab("t.0", "Draft 2", "draft"),
        _tab("t.ul3yzv5xed4w", "Final", "final", [_tab("t.child", "Notes", "notes")]),
    ],
}


def test_parse_ref_extracts_the_tab_from_the_url():
    assert parse_ref(URL) == (DOC_ID, "t.ul3yzv5xed4w")


def test_parse_ref_accepts_a_bare_id():
    assert parse_ref(DOC_ID) == (DOC_ID, None)


def test_parse_ref_without_a_tab():
    assert parse_ref(f"https://docs.google.com/document/d/{DOC_ID}/edit") == (DOC_ID, None)


def test_the_requested_tab_wins_over_the_first_one():
    chosen = select_tab(MULTI_TAB, "t.ul3yzv5xed4w")
    assert chosen["body"]["content"][0]["marker"] == "final"
    assert chosen["tabTitle"] == "Final"


def test_child_tabs_are_selectable():
    assert select_tab(MULTI_TAB, "t.child")["tabTitle"] == "Notes"


def test_an_ambiguous_document_refuses_to_guess():
    with pytest.raises(TabNotFound) as e:
        select_tab(MULTI_TAB, None)
    assert "Draft 2" in str(e.value) and "Final" in str(e.value)


def test_an_unknown_tab_lists_what_is_available():
    with pytest.raises(TabNotFound) as e:
        select_tab(MULTI_TAB, "t.nope")
    assert "t.ul3yzv5xed4w" in str(e.value)


def test_a_single_tab_document_needs_no_choice():
    single = {"title": "x", "tabs": [_tab("t.only", "Only", "only")]}
    assert select_tab(single, None)["body"]["content"][0]["marker"] == "only"


def test_a_document_with_no_tabs_is_passed_through():
    plain = {"title": "x", "body": {"content": [{"marker": "plain"}]}}
    assert select_tab(plain, None) is plain


# ---- credentials ----------------------------------------------------


def test_service_account_credentials_are_used_when_the_environment_names_them(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """CI has no browser to open and nobody to click,
    so the interactive flow must not be what runs there."""
    import google.auth

    from eta_publish import fetch as fetch_module

    sentinel = object()

    def fake_default(scopes: list[str]) -> tuple[object, str]:
        assert scopes == SCOPES
        return sentinel, "eta-publish"

    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(tmp_path / "key.json"))
    monkeypatch.setattr(google.auth, "default", fake_default)
    assert fetch_module._credentials() is sentinel


def test_without_the_environment_variable_nothing_is_ambient(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from eta_publish import fetch as fetch_module

    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    assert fetch_module._ambient_credentials() is None


def test_a_suggestion_is_counted_once_however_much_it_touches() -> None:
    """One suggestion over a sentence marks every run in it:
    the real document carries 240 insertion marks and far fewer suggestions."""
    from eta_publish.fetch import _suggestion_ids

    document = {
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {"textRun": {"suggestedInsertionIds": ["s.1"]}},
                            {"textRun": {"suggestedInsertionIds": ["s.1"]}},
                            {"textRun": {"suggestedDeletionIds": ["s.2"]}},
                        ]
                    }
                },
                {"paragraph": {"suggestedParagraphStyleChanges": {"s.3": {"bold": True}}}},
            ]
        }
    }
    assert _suggestion_ids(document) == {"s.1", "s.2", "s.3"}


def test_a_document_with_nothing_suggested_counts_none() -> None:
    from eta_publish.fetch import _suggestion_ids

    assert _suggestion_ids({"body": {"content": [{"paragraph": {"elements": []}}]}}) == set()


def test_a_service_account_is_not_asked_about_the_review(monkeypatch: pytest.MonkeyPatch) -> None:
    """It is refused the suggestions outright,
    and for the comments the export answers, renders a document with none in it
    because it cannot see any, and returns a nought no retry would catch."""
    import eta_publish.fetch as fetch

    def boom(*args: object, **kwargs: object) -> object:
        raise AssertionError("a service account must not be asked this")

    def whole_document(doc_id: str, suggestions: str = "rejected") -> JsonObject:
        return {"tabs": []}

    def one_tab(document: JsonObject, wanted: str | None) -> JsonObject:
        return {"body": {}}

    monkeypatch.setattr(fetch, "_ambient_credentials", lambda: object())
    monkeypatch.setattr(fetch, "fetch_document", whole_document)
    monkeypatch.setattr(fetch, "select_tab", one_tab)
    monkeypatch.setattr(fetch, "open_suggestions", boom)
    monkeypatch.setattr(fetch, "open_comments_on_tab", boom)

    document = fetch.fetch("https://docs.google.com/document/d/abc/edit")
    assert "openSuggestions" not in document
    assert "openComments" not in document


def test_keeping_the_last_counts_is_said_out_loud(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`gcloud auth application-default login` is enough to stop these being counted,
    and a build that quietly republishes the last numbers looks like one that checked."""
    import eta_publish.fetch as fetch

    def whole_document(doc_id: str, suggestions: str = "rejected") -> JsonObject:
        return {"tabs": []}

    def one_tab(document: JsonObject, wanted: str | None) -> JsonObject:
        return {"body": {}}

    monkeypatch.setattr(fetch, "_ambient_credentials", lambda: object())
    monkeypatch.setattr(fetch, "fetch_document", whole_document)
    monkeypatch.setattr(fetch, "select_tab", one_tab)

    fetch.fetch("https://docs.google.com/document/d/abc/edit")
    assert "not asking about suggestions or comments" in capsys.readouterr().err
