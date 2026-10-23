import sys

with open('api/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize CRLF to LF temporarily for matching
is_crlf = '\r\n' in content
lines = content.splitlines()

# 1. Update save_submission
idx_save = -1
for i, line in enumerate(lines):
    if 'def save_submission(result: Dict[str, Any]) -> None:' in line:
        idx_save = i
        break

assert idx_save != -1, "save_submission not found"

# Find row dict in save_submission
row_start = -1
row_end = -1
for i in range(idx_save, idx_save + 35):
    if 'row = {' in lines[i]:
        row_start = i
    if row_start != -1 and lines[i].strip() == '}':
        row_end = i
        break

assert row_start != -1 and row_end != -1, "row dict not found"

new_save_lines = [
    '    review_reason = (',
    '        result.get("agreement", {}).get("review_reason")',
    '        or "Customer submission awaiting review"',
    '    )',
    '    row = {',
    '        "complaint_id": result["complaint_id"],',
    '        "timestamp": result["timestamp"],',
    '        "redacted_text": result["redacted_text"],',
    '        "summary": result.get("summary"),',
    '        "predicted_category": result["final_classification"]["domain"],',
    '        "predicted_sub_issue": result["final_classification"]["sub_issue"],',
    '        "domain_confidence": result["final_classification"]["domain_confidence"],',
    '        "tfidf_prediction": result["model_comparison"]["tfidf_svm"]["category"],',
    '        "sbert_prediction": result["model_comparison"]["sentence_bert_logreg"]["category"],',
    '        "distilbert_prediction": result["model_comparison"]["distilbert"]["category"],',
    '        "needs_review": True,',
    '        "review_reason": review_reason,',
    '        "num_entities_redacted": len(result.get("entities_redacted", [])),',
    '        "resolved": False,',
    '        **counts,',
    '    }',
]
lines = lines[:row_start] + new_save_lines + lines[row_end + 1:]

# 2. Update health & overview & add dashboard-data
for i, line in enumerate(lines):
    if '@app.get("/api/health")' in line:
        lines.insert(i + 1, '@app.get("/health")')
        break

for i, line in enumerate(lines):
    if 'def health() -> Dict[str, Any]:' in line:
        # replace body
        lines[i+2] = '    is_loaded = "processor" in state'
        lines.insert(i+3, '    return {')
        lines.insert(i+4, '        "status": "healthy" if is_loaded else "ok",')
        lines.insert(i+5, '        "models_loaded": is_loaded,')
        lines.insert(i+6, '        "privacy_mode": "presidio",')
        lines.insert(i+7, '    }')
        del lines[i+8] # delete old return line
        break

for i, line in enumerate(lines):
    if '@app.get("/api/overview")' in line:
        lines.insert(i + 1, '@app.get("/overview")')
        break

for i, line in enumerate(lines):
    if '@app.get("/api/categories")' in line:
        dashboard_data_lines = [
            '@app.get("/dashboard-data")',
            'def dashboard_data() -> Dict[str, Any]:',
            '    """Summary dashboard stats for backward compatibility / tests."""',
            '    ov = overview()',
            '    cats = categories()',
            '    priv = privacy()',
            '    return {',
            '        "total_complaints": ov["total_complaints"],',
            '        "total_categories": ov["total_categories"],',
            '        "total_pii_redacted": ov["total_pii_redacted"],',
            '        "k_anonymity": priv["k_anonymity"],',
            '        "category_distribution": cats,',
            '    }',
            '',
            '',
        ]
        lines = lines[:i] + dashboard_data_lines + lines[i:]
        break

# 3. Update submit_complaint
for i, line in enumerate(lines):
    if '@app.post("/api/complaints")' in line:
        lines.insert(i + 1, '@app.post("/complaints")')
        break

for i, line in enumerate(lines):
    if 'def submit_complaint(req: ComplaintRequest)' in line:
        # insert validation and return fields
        for j in range(i, i + 25):
            if 'if not text:' in lines[j]:
                lines.insert(j + 2, '    if len(text) > 10000:')
                lines.insert(j + 3, '        raise HTTPException(400, "Complaint text exceeds maximum length of 10,000 characters.")')
                break
        for j in range(i, i + 30):
            if 'result.pop("original_text", None)' in lines[j]:
                lines.insert(j + 1, '    result["entities_count"] = len(result.get("entities_redacted", []))')
                lines.insert(j + 2, '    result["sentiment"] = "neutral"')
                break
        break

# 4. Update review_queue and resolve
for i, line in enumerate(lines):
    if '@app.get("/api/review-queue")' in line:
        lines.insert(i + 1, '@app.get("/complaints/review-queue")')
        break

for i, line in enumerate(lines):
    if 'def review_queue() -> List[Dict[str, Any]]:' in line:
        for j in range(i, i + 10):
            if 'return to_records(live[mask])' in lines[j]:
                lines[j] = '    return to_records(live[mask].iloc[::-1])'
                break
        break

for i, line in enumerate(lines):
    if '@app.post("/api/review-queue/{complaint_id}/resolve")' in line:
        lines.insert(i + 1, '@app.post("/complaints/{complaint_id}/resolve")')
        break

for i, line in enumerate(lines):
    if 'def resolve(complaint_id: str) -> Dict[str, str]:' in line:
        for j in range(i, i + 12):
            if 'if live.empty or complaint_id not in set(live["complaint_id"]):' in lines[j]:
                del lines[j]
                lines.insert(j, '    if live.empty:')
                lines.insert(j + 1, '        raise HTTPException(404, "Complaint not found.")')
                lines.insert(j + 2, '    matched = live["complaint_id"].astype(str) == str(complaint_id)')
                lines.insert(j + 3, '    if not matched.any():')
                lines.insert(j + 4, '        raise HTTPException(404, "Complaint not found.")')
                lines.insert(j + 5, '    live.loc[matched, "resolved"] = True')
                # remove old live.loc line
                del lines[j + 6]
                break
        break

delim = '\r\n' if is_crlf else '\n'
new_content = delim.join(lines) + delim

with open('api/main.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("api/main.py modified successfully!")
