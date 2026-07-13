from factorypulse.rag.embeddings import embed_text
from factorypulse.rag.retrieve import extract_fault_codes


def test_embed_deterministic():
    a = embed_text("E-310 bearing acceleration")
    b = embed_text("E-310 bearing acceleration")
    assert a == b
    assert len(a) == 384


def test_extract_fault_codes():
    assert "E-310" in extract_fault_codes("alarm E-310 on fan")
    assert "E-AUDIO" in extract_fault_codes("heard E-AUDIO signature")
