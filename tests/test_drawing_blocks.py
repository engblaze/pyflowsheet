from pyflowsheet.backends import SvgContext
from pyflowsheet.drawing import GeneralNotes, RevisionBlock, TitleBlock
from pyflowsheet.schema.models import MetadataRevisionSchema, MetadataSchema


def test_title_block_render(tmp_path):
    out_svg = tmp_path / "test_title.svg"
    ctx = SvgContext(str(out_svg))
    meta = {
        "title": "TEST TITLE",
        "drawing_number": "DWG-123",
        "revision": "B",
        "cage_code": "1A2B3",
        "drawn_by": "E. Vance",
        "approved_by": "H. Green",
    }
    tb = TitleBlock(meta, rect=((880.0, 660.0), (1260.0, 820.0)))
    tb.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="title_block"' in content
    assert "TEST TITLE" in content
    assert "DWG-123" in content
    assert "1A2B3" in content
    assert "E. Vance" in content


def test_revision_block_render(tmp_path):
    out_svg = tmp_path / "test_rev.svg"
    ctx = SvgContext(str(out_svg))
    revs = [
        {
            "zone": "-",
            "rev": "A",
            "description": "INITIAL RELEASE",
            "date": "2026-09-01",
            "approved_by": "H. Green",
        }
    ]
    rb = RevisionBlock(rect=((880.0, -20.0), (1260.0, 50.0)), revisions=revs)
    rb.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="revision_block"' in content
    assert "REVISIONS" in content
    assert "INITIAL RELEASE" in content


def test_general_notes_render(tmp_path):
    out_svg = tmp_path / "test_notes.svg"
    ctx = SvgContext(str(out_svg))
    notes = ["NOTE ONE", "NOTE TWO"]
    nb = GeneralNotes(notes=notes, rect=((-30.0, 660.0), (860.0, 820.0)))
    nb.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="drawing_notes"' in content
    assert "GENERAL PROCESS NOTES &amp; SPECIFICATIONS" in content
    assert "NOTE ONE" in content


def test_title_block_with_metadata_schema(tmp_path):
    out_svg = tmp_path / "test_title_schema.svg"
    ctx = SvgContext(str(out_svg))
    meta_schema = MetadataSchema(
        title="SCHEMA DRIVEN FLOWSHEET",
        subtitle="ADVANCED WATER SYSTEM",
        drawing_number="DWG-SCHEMA-001",
        revision="C",
        cage_code="98765",
        drawn_by="A. Turing",
        checked_by="K. Shannon",
        approved_by="J. von Neumann",
        sheet_size="D",
        scale="1:100",
        sheet="2 OF 3",
        status="APPROVED FOR CONSTRUCTION",
        units="INCHES",
        projection="FIRST ANGLE",
        code_standard="ISO 10628",
    )
    tb = TitleBlock(meta_schema)
    tb.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="title_block"' in content
    assert "SCHEMA DRIVEN FLOWSHEET" in content
    assert "ADVANCED WATER SYSTEM" in content
    assert "DWG-SCHEMA-001" in content
    assert "98765" in content
    assert "A. Turing" in content
    assert "K. Shannon" in content
    assert "J. von Neumann" in content
    assert "1:100" in content
    assert "2 OF 3" in content
    assert "APPROVED FOR CONSTRUCTION" in content
    assert "INCHES" in content
    assert "FIRST ANGLE PROJECTION" in content
    assert "ISO 10628" in content


def test_title_block_defaults(tmp_path):
    out_svg = tmp_path / "test_title_defaults.svg"
    ctx = SvgContext(str(out_svg))
    tb = TitleBlock()
    tb.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="title_block"' in content
    assert "ADVANCED WATER SYSTEMS ENGINEERING" in content
    assert "WATER TREATMENT PROCESS FLOW DIAGRAM" in content
    assert "1A2B3" in content
    assert "E. Vance" in content


def test_revision_block_empty_and_models(tmp_path):
    out_svg = tmp_path / "test_rev_schema.svg"
    ctx = SvgContext(str(out_svg))
    revs = [
        MetadataRevisionSchema(
            zone="B-2",
            rev="A",
            description="FIRST REVISION",
            date="2026-09-10",
            approved_by="Alice",
        ),
        MetadataRevisionSchema(
            zone="C-4",
            rev="B",
            description="SECOND REVISION",
            date="2026-09-15",
            approved_by="Bob",
        ),
    ]
    rb = RevisionBlock(revisions=revs)
    rb.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="revision_block"' in content
    assert "B-2" in content
    assert "FIRST REVISION" in content
    assert "C-4" in content
    assert "SECOND REVISION" in content
    assert "Alice" in content
    assert "Bob" in content

    # Test empty revisions
    rb_empty = RevisionBlock()
    assert rb_empty.revisions == []


def test_general_notes_defaults(tmp_path):
    out_svg = tmp_path / "test_notes_defaults.svg"
    ctx = SvgContext(str(out_svg))
    nb = GeneralNotes()
    nb.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="drawing_notes"' in content
    assert "GENERAL PROCESS NOTES &amp; SPECIFICATIONS" in content
    assert "ALL PROCESS PIPING SIZED FOR 100 M^3/HR NOMINAL LIQUID THROUGHPUT." in content
    assert "STANDARDS APPLICABLE: ANSI/ASME Y14.1" in content


def test_general_notes_empty(tmp_path):
    out_svg = tmp_path / "test_notes_empty.svg"
    ctx = SvgContext(str(out_svg))
    nb = GeneralNotes(notes=[])
    nb.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="drawing_notes"' in content
    assert "GENERAL PROCESS NOTES &amp; SPECIFICATIONS" in content
    assert "ALL PROCESS PIPING" not in content
    assert nb.notes == []
