"""Naming must not move when the document is edited around it.

These tests use headings that genuinely collide, since the collision
branch is the only one that can be positional.
"""

from eta_publish.naming import AnchorAllocator, image_filename, slugify

# Two distinct headings that slugify identically.
COST_COLON = "Cost: Overview"
COST_PLAIN = "Cost Overview"


def test_slugify_strips_punctuation_and_accents():
    assert slugify("The Elephants in the Room") == "the-elephants-in-the-room"
    assert slugify("Cost: $7.7B!") == "cost-77b"
    assert slugify("") == "section"


def test_the_common_case_gets_a_clean_anchor():
    a = AnchorAllocator(["The Elephants in the Room", "Station Depth"])
    assert a.allocate("Station Depth") == "station-depth"


def test_repeated_heading_text_reuses_its_anchor():
    a = AnchorAllocator(["Overview", "Overview"])
    assert a.allocate("Overview") == a.allocate("Overview") == "overview"


def test_colliding_anchors_survive_reordering():
    """The bug this guards: giving the bare slug to whichever heading
    claims it first is still positional, so swapping two colliding
    headings moves both of their anchors."""
    first = AnchorAllocator([COST_COLON, COST_PLAIN])
    second = AnchorAllocator([COST_PLAIN, COST_COLON])
    assert first.allocate(COST_COLON) == second.allocate(COST_COLON)
    assert first.allocate(COST_PLAIN) == second.allocate(COST_PLAIN)
    assert first.allocate(COST_COLON) != first.allocate(COST_PLAIN)


def test_colliding_anchors_survive_an_unrelated_insertion():
    before = AnchorAllocator([COST_COLON, COST_PLAIN])
    after = AnchorAllocator([COST_COLON, "Station Depth", COST_PLAIN])
    assert before.allocate(COST_PLAIN) == after.allocate(COST_PLAIN)


def test_an_override_wins_and_is_not_treated_as_a_collision():
    a = AnchorAllocator(
        [COST_COLON, COST_PLAIN], overrides={COST_COLON: "elephants"}
    )
    assert a.allocate(COST_COLON) == "elephants"
    # With the override removed from contention, nothing collides any more.
    assert a.allocate(COST_PLAIN) == "cost-overview"


def test_image_names_depend_only_on_the_docs_object_id():
    assert image_filename("io.7", ".png") == image_filename("io.7", ".png")
    assert image_filename("io.7", ".png") != image_filename("io.8", ".png")
