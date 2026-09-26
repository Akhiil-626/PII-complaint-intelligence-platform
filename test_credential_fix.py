"""
test_credential_fix.py
Verifies that CredentialRecognizer detects BOTH username and password in
natural-language complaint text, after the regex fix.
"""
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from redaction.custom_recognizers import CredentialRecognizer

# ── Build a minimal AnalyzerEngine with only our custom recognizer ──────────
provider = NlpEngineProvider(nlp_configuration={
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
})
nlp_engine = provider.create_engine()

analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
# Remove all built-in recognizers so only ours fires
analyzer.registry.remove_recognizer("SpacyRecognizer")
for rec_name in [r.name for r in analyzer.registry.recognizers]:
    try:
        analyzer.registry.remove_recognizer(rec_name)
    except Exception:
        pass

analyzer.registry.add_recognizer(CredentialRecognizer())

# ── Test text ───────────────────────────────────────────────────────────────
test_text = (
    "My username is john_doe99 and my password is hunter2, "
    "please help me reset it."
)

print("=" * 65)
print("Test text:")
print(" ", test_text)
print("=" * 65)

results = analyzer.analyze(text=test_text, language="en")
results.sort(key=lambda r: r.start)

print(f"\nResults ({len(results)} found):")
if results:
    for r in results:
        span = test_text[r.start:r.end]
        print(f"  [{r.entity_type}]  '{span}'  "
              f"start={r.start} end={r.end}  score={r.score:.2f}")
else:
    print("  (none)")

# ── Assertion ───────────────────────────────────────────────────────────────
entity_types = [r.entity_type for r in results]
spans         = [test_text[r.start:r.end] for r in results]

assert entity_types.count("CREDENTIAL") >= 2, (
    f"Expected at least 2 CREDENTIAL entities, got {entity_types}"
)
# Both credentials should appear in the detected spans
assert any("username" in s.lower() for s in spans), "username not detected"
assert any("password" in s.lower() for s in spans), "password not detected"

print("\n✓ PASS — both CREDENTIAL entities (username AND password) detected.")

# ── Also test key-value style to confirm it still works ──────────────────
print("\n--- Bonus: key-value style (regression check) ---")
kv_text = "username: john_doe99 password=hunter2"
kv_results = analyzer.analyze(text=kv_text, language="en")
kv_results.sort(key=lambda r: r.start)
for r in kv_results:
    print(f"  [{r.entity_type}]  '{kv_text[r.start:r.end]}'  score={r.score:.2f}")

assert len(kv_results) >= 2, "Expected 2 hits for key-value text"
print("✓ PASS — key-value style still detected correctly.")
