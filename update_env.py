import os

env_path = '.env'
new_keys = {
    'APCA_API_KEY_ID': 'PKOCEG347D3IBEEKCTIOWTAG46',
    'APCA_API_SECRET_KEY': 'CkYhHiVAZWjSxKMEDH5n71HWhFhJePtkVFp6cgqTE718'
}

# Read existing
lines = []
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        lines = f.readlines()

# Update or Append
updated_lines = []
keys_updated = set()

for line in lines:
    key_match = False
    for k, v in new_keys.items():
        if line.startswith(f"{k}="):
            updated_lines.append(f"{k}={v}\n")
            keys_updated.add(k)
            key_match = True
            break
    if not key_match:
        updated_lines.append(line)

# Append missing
for k, v in new_keys.items():
    if k not in keys_updated:
        updated_lines.append(f"{k}={v}\n")

with open(env_path, 'w') as f:
    f.writelines(updated_lines)

print("✅ .env updated with Alpaca Keys.")
