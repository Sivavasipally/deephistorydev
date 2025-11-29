"""Test script to demonstrate credential encoding with special characters."""

from urllib.parse import quote

# Test cases with various special characters
test_cases = [
    ("simple", "password123", "password123"),
    ("with_at", "P@ssw0rd", "P%40ssw0rd"),
    ("with_hash", "Pass#123", "Pass%23123"),
    ("with_dollar", "P$$word", "P%24%24word"),
    ("with_ampersand", "Pass&word", "Pass%26word"),
    ("complex", "P@$$w0rd#123!", "P%40%24%24w0rd%23123%21"),
    ("bitbucket_app", "ATBBx8Fk3mP#QzW$9", "ATBBx8Fk3mP%23QzW%249"),
    ("spaces", "My Pass 123", "My%20Pass%20123"),
    ("special_mix", "abc{123}[456]", "abc%7B123%7D%5B456%5D"),
]

print("=" * 80)
print("Credential Encoding Test - Special Characters")
print("=" * 80)
print()

for test_name, original, expected in test_cases:
    encoded = quote(original, safe='')
    status = "[PASS]" if encoded == expected else "[FAIL]"

    print(f"{status} | {test_name}")
    print(f"  Original: {original}")
    print(f"  Encoded:  {encoded}")
    print(f"  Expected: {expected}")
    print()

# Demonstrate URL construction
print("=" * 80)
print("Example URL Construction")
print("=" * 80)
print()

username = "john.doe"
password = "MyP@ssw0rd#2024!"
repo_url = "https://bitbucket.org/workspace/repo.git"

encoded_username = quote(username, safe='')
encoded_password = quote(password, safe='')

authenticated_url = f"https://{encoded_username}:{encoded_password}@bitbucket.org/workspace/repo.git"

print(f"Username: {username}")
print(f"Password: {password}")
print(f"Repository: {repo_url}")
print()
print(f"Encoded Username: {encoded_username}")
print(f"Encoded Password: {encoded_password}")
print()
print(f"Authenticated URL:")
print(f"{authenticated_url}")
print()

print("=" * 80)
print("All special characters are automatically handled!")
print("=" * 80)
