"""Naming must be stable under insertion; that is the whole point of it."""

from eta_publish.naming import AnchorAllocator, image_filename, slugify


def test_slugify_strips_punctuation_and_accents():
    assert slugify("The Elephants in the Room") == "the-elephants-in-the-room"
    assert slugify("Cost: $7.7B!") == "cost-77b"
    assert slugify("") == "section"


def test_repeated_heading_text_reuses_its_anchor():
    a = AnchorAllocator()
    assert a.allocate("Overview") == "overview"
    assert a.allocate("Overview") == "overview"


def test_colliding_anchors_do_not_move_when_a_heading_is_inserted_before():
    """A positional counter would reassign `overview-2` to a new section."""
    before = AnchorAllocator()
    before.allocate("Overview")
    ground = before.allocate("Ground Conditions")

    after = AnchorAllocator()
    after.allocate("Overview")
    after.allocate("Station Depth")  # inserted earlier in a later draft
    assert after.allocate("Ground Conditions") == ground


def test_image_names_depend_only_on_the_docs_object_id():
    assert image_filename("io.7", ".png") == image_filename("io.7", ".png")
    assert image_filename("io.7", ".png") != image_filename("io.8", ".png")
