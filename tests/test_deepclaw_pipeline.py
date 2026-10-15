import pytest
from backend.collectors.html_parser import HTMLParser
from backend.processors.fact_extractor import FactExtractor
from backend.processors.contradiction_detector import ContradictionDetector
from backend.db.models import Session as SessionModel, Source, Fact

def test_html_parser_cleans_content():
    raw_html = "<html><body><h1>Tech Report</h1><p>Autonomous AI agents are transforming DevOps.</p><script>alert(1);</script></body></html>"
    cleaned = HTMLParser.clean_html_content(raw_html)
    assert "Autonomous AI agents" in cleaned
    assert "<script>" not in cleaned

@pytest.mark.asyncio
async def test_fact_extractor_workflow():
    session = SessionModel(id="test_sess_01", topic="AI Agents", depth=2)
    source = Source(
        id="src_01",
        session_id="test_sess_01",
        url="https://example.com/ai",
        title="AI Evolution",
        content="<p>OpenAI launched GPT-4 in 2023. Anthropic released Claude 3 in 2024.</p>"
    )
    extractor = FactExtractor(session=session)
    facts = await extractor.extract_from_source(source)
    assert isinstance(facts, list)

@pytest.mark.asyncio
async def test_contradiction_detector_init():
    session = SessionModel(id="test_sess_02", topic="Quantum Computing", depth=2)
    detector = ContradictionDetector(session=session)
    await detector.build_fact_database([])
    assert isinstance(detector.fact_database, dict)
