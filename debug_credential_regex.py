"""
Step 2 & 4: Standalone regex diagnostic for CredentialRecognizer
Runs entirely in Python's re module — no Presidio involved.
"""
import re

test_text = "My username is john_doe99 and my password is hunter2, please help me reset it."

print("=" * 65)
print("TEST TEXT:", test_text)
print("=" * 65)

# ── Step 2: Run the ORIGINAL pattern exactly as it appears in the file ──
print("\n--- STEP 2: Original pattern (as saved in the file) ---")
pattern_original = r"(?i)\b(password|pwd|pass|username|user\s*name|login|user\s*id|userid)\s*[:=]\s*\S+"
matches = re.findall(pattern_original, test_text)
print("re.findall() => Matches found:", matches)

matches_full = list(re.finditer(pattern_original, test_text))
for m in matches_full:
    print(f"  Full match: '{m.group(0)}'  at position {m.span()}")
if not matches_full:
    print("  NO MATCHES AT ALL")

# ── Step 4: Root-cause analysis ──
print("\n--- STEP 4: Root-cause analysis ---")
print("The test text uses 'username IS john_doe99' and 'password IS hunter2'.")
print("The separator is the English word 'is' (with spaces), NOT a colon ':' or equals '='.")
print("The original pattern's separator clause is:  \\s*[:=]\\s*")
print("This requires a literal ':' or '=' — so neither credential matches.")
print()

# Verify: original pattern DOES work when the separator IS a colon/equals
test_kv = "username: john_doe99 and password: hunter2"
matches_kv = list(re.finditer(pattern_original, test_kv))
print("Sanity-check — original pattern on key:value text:")
print("  Text:", test_kv)
for m in matches_kv:
    print(f"  Full match: '{m.group(0)}'  at position {m.span()}")

print()
print("Conclusion: The regex is correct for key:value style but does NOT handle")
print("            natural-language form 'keyword IS value'.")

# ── Corrected pattern ──
print("\n--- STEP 4 (continued): Corrected pattern ---")
# Allow ":", "=", OR "is"/"are" as separators
pattern_fixed = (
    r"(?i)\b"
    r"(password|pwd|pass|username|user\s*name|login|user\s*id|userid)"
    r"\s*(?:[:=]|\bis\b|\bare\b)\s*"
    r"(\S+)"
)
print("Fixed pattern:")
print(" ", pattern_fixed)
print()

matches_fixed = list(re.finditer(pattern_fixed, test_text))
print("re.finditer() on original test text:")
for m in matches_fixed:
    print(f"  Full match: '{m.group(0)}'  at position {m.span()}")
if not matches_fixed:
    print("  NO MATCHES")

# Also verify key:value still works with the fixed pattern
matches_fixed_kv = list(re.finditer(pattern_fixed, test_kv))
print("\nre.finditer() on key:value text:")
for m in matches_fixed_kv:
    print(f"  Full match: '{m.group(0)}'  at position {m.span()}")
if not matches_fixed_kv:
    print("  NO MATCHES")

# Additional edge-case tests
print("\n--- Edge-case tests on fixed pattern ---")
edge_cases = [
    "pwd=s3cr3t!",
    "login: admin123",
    "My user name is bob_42",
    "userid=USR99",
    "password are wrong",          # unusual but pattern handles it
]
for tc in edge_cases:
    ms = [m.group(0) for m in re.finditer(pattern_fixed, tc)]
    print(f"  {tc!r:45s} -> {ms}")
