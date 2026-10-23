with open('api/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if 'live.loc[live["complaint_id"] == complaint_id, "resolved"] = True' in line:
        continue
    new_lines.append(line)

with open('api/main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Fixed!')
