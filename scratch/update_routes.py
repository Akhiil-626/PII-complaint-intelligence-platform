with open('api/routes/complaints.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '"needs_review": result["agreement"]["needs_review"],',
    '"needs_review": True,'
)
text = text.replace(
    '"review_reason": result["agreement"].get("review_reason") or "",',
    '"review_reason": result["agreement"].get("review_reason") or "Customer submission awaiting review",'
)
text = text.replace(
    'flagged = df[(df["needs_review"] == True) & (df["resolved"] != True)]',
    'flagged = df[(df["needs_review"] == True) & (df["resolved"] != True)].iloc[::-1]'
)

with open('api/routes/complaints.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("api/routes/complaints.py updated!")
