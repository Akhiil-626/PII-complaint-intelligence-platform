from src.redaction.presidio_pipeline import PresidioRedactionPipeline

pipeline = PresidioRedactionPipeline()

test_text = "My username is john_doe99 and my password is hunter2, please help me reset it."

result = pipeline.redact_with_metadata(test_text)

print("Redacted text:", result["redacted_text"])
print("\nEntities found:")
for entity in result["entities"]:
    print(f"  {entity['entity_type']}: '{entity['text']}'")