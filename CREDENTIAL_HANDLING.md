# Credential Handling Guide

## Overview

The Git History Deep Analyzer properly handles special characters in Git credentials using URL encoding (percent encoding) to ensure passwords with special characters work correctly.

## Special Character Support

### Supported Characters

The following special characters in passwords are automatically encoded:

| Character | URL Encoded | Description |
|-----------|-------------|-------------|
| `@` | `%40` | At sign |
| `#` | `%23` | Hash/pound |
| `$` | `%24` | Dollar sign |
| `%` | `%25` | Percent |
| `&` | `%26` | Ampersand |
| `+` | `%2B` | Plus |
| `=` | `%3D` | Equals |
| `:` | `%3A` | Colon |
| `/` | `%2F` | Forward slash |
| `?` | `%3F` | Question mark |
| `!` | `%21` | Exclamation |
| `*` | `%2A` | Asterisk |
| `'` | `%27` | Single quote |
| `"` | `%22` | Double quote |
| `<` | `%3C` | Less than |
| `>` | `%3E` | Greater than |
| `{` | `%7B` | Left brace |
| `}` | `%7D` | Right brace |
| `[` | `%5B` | Left bracket |
| `]` | `%5D` | Right bracket |
| `\|` | `%7C` | Pipe |
| `\` | `%5C` | Backslash |
| `^` | `%5E` | Caret |
| `` ` `` | `%60` | Backtick |
| ` ` | `%20` | Space |

**All special characters are automatically handled** - you don't need to encode them manually!

## Usage

### 1. With Special Characters in Password

Simply enter your password as-is in the `.env` file:

```ini
# Example with special characters
GIT_USERNAME=myuser
GIT_PASSWORD=MyP@ssw0rd#2024!

# Works with complex passwords
GIT_PASSWORD=P@$$w0rd&T3st#123!

# Even with unusual characters
GIT_PASSWORD=abc{123}def[456]ghi
```

### 2. Application Automatically Encodes

The application automatically encodes your credentials when constructing Git URLs:

```python
# Your password: MyP@ssw0rd#2024!
# Automatically becomes: MyP%40ssw0rd%232024%21
# In URL: https://user:MyP%40ssw0rd%232024%21@bitbucket.org/repo.git
```

### 3. No Manual Encoding Needed

**DO NOT** manually encode your password in `.env`:

```ini
# ❌ WRONG - Don't do this
GIT_PASSWORD=MyP%40ssw0rd%232024%21

# ✅ CORRECT - Enter as-is
GIT_PASSWORD=MyP@ssw0rd#2024!
```

## Examples

### Example 1: Bitbucket App Password

Bitbucket app passwords often contain special characters:

```ini
# Bitbucket app password (example)
GIT_USERNAME=john.doe
GIT_PASSWORD=ATBBx8Fk3mP#QzW$9Yh2

# Automatically encoded to:
# ATBBx8Fk3mP%23QzW%249Yh2
```

### Example 2: GitHub Personal Access Token

GitHub tokens are alphanumeric, but the encoding works for any format:

```ini
# GitHub token
GIT_USERNAME=johndoe
GIT_PASSWORD=ghp_1234567890abcdefghij

# No special chars, used as-is
```

### Example 3: Complex Password

Password with multiple special characters:

```ini
GIT_USERNAME=admin
GIT_PASSWORD=P@$$&w0rd!#2024

# Automatically encoded to:
# P%40%24%24%26w0rd%21%232024
```

### Example 4: Password with Spaces

Even spaces are handled:

```ini
# Password with spaces (not recommended, but works)
GIT_PASSWORD=My Secret Pass 123!

# Automatically encoded to:
# My%20Secret%20Pass%20123%21
```

## How It Works

### Under the Hood

```python
from urllib.parse import quote

# Your credentials
username = "john.doe"
password = "MyP@ssw0rd#123!"

# Automatic encoding
encoded_username = quote(username, safe='')  # john.doe
encoded_password = quote(password, safe='')   # MyP%40ssw0rd%23123%21

# Constructed URL
url = f"https://{encoded_username}:{encoded_password}@bitbucket.org/repo.git"
# Result: https://john.doe:MyP%40ssw0rd%23123%21@bitbucket.org/repo.git
```

### Encoding Process

1. **Read credentials** from `.env` file
2. **Parse clone URL** using `urlparse()`
3. **Encode username** using `quote(username, safe='')`
4. **Encode password** using `quote(password, safe='')`
5. **Construct authenticated URL** with encoded credentials
6. **Pass to GitPython** for cloning

## Platform-Specific Notes

### Bitbucket

**App Passwords**:
- Generated format: `ATBBxxxxxxxxxxxxxxxxx`
- May contain: Letters, numbers, no special chars typically
- Safe to use as-is

**Personal Access Tokens**:
- May contain special characters
- Automatically encoded

**Username**:
- Typically: `username` or `email@domain.com`
- Email addresses with `@` are properly encoded

### GitHub

**Personal Access Tokens**:
- Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- Contains: Letters and numbers only
- No encoding needed but works regardless

**Fine-Grained Tokens**:
- Format: `github_pat_xxxxxxxxxxxxxx`
- Alphanumeric only

### GitLab

**Personal Access Tokens**:
- Format: Various, may contain special chars
- Automatically encoded

### Generic Git Servers

Works with any Git server that supports HTTP(S) authentication.

## Troubleshooting

### "Authentication failed"

**Possible Causes**:
1. Incorrect username or password
2. Password expired
3. Account locked
4. Insufficient permissions

**Solution**:
```bash
# Test credentials manually
git clone https://username:password@bitbucket.org/workspace/repo.git test-clone

# If this fails, credentials are wrong
# If it works, issue is elsewhere
```

### "Invalid characters in URL"

This should **not** happen with proper encoding. If you see this:

1. Check if you manually encoded the password
2. Verify `.env` file format is correct
3. Ensure no invisible characters in password

### Password Not Working

**Checklist**:
- ✅ Password is correct (test in web UI)
- ✅ Password is not manually encoded
- ✅ No extra spaces before/after password
- ✅ Using correct username
- ✅ Token/password has required permissions

### Testing Credentials

```bash
# Test with curl
curl -u "username:password" https://bitbucket.org/api/2.0/user

# Should return user info if credentials are correct
```

## Security Best Practices

### 1. Use Tokens, Not Passwords

**Recommended**:
```ini
# Use app password or personal access token
GIT_PASSWORD=ATBBx8Fk3mP#QzW$9Yh2
```

**Not Recommended**:
```ini
# Don't use account password
GIT_PASSWORD=MyAccountPassword123!
```

### 2. Limit Token Permissions

- Only grant "Read" permission for repositories
- Don't grant unnecessary scopes
- Create separate tokens for different purposes

### 3. Rotate Credentials Regularly

```bash
# Rotate every 90 days
# 1. Generate new token
# 2. Update .env
# 3. Test
# 4. Revoke old token
```

### 4. Never Commit `.env`

```bash
# Verify .env is in .gitignore
cat .gitignore | grep .env

# Should show:
# .env
```

### 5. Use Environment Variables in Production

Instead of `.env` file:

```bash
# Set environment variables
export GIT_USERNAME=myuser
export GIT_PASSWORD=MyP@ssw0rd#123!

# Run application
python cli.py repos.csv
```

## Common Password Patterns

### Strong Passwords

Examples of strong passwords that work perfectly:

```ini
# Mix of everything
GIT_PASSWORD=Xy9$mK#2pL@8qW!

# Longer with special chars
GIT_PASSWORD=MyCompany@2024#SecurePass!

# Using brackets and braces
GIT_PASSWORD=P@ss{2024}[Secure]#123!
```

### Avoid These Patterns

**Not recommended** (security reasons):

```ini
# Too simple
GIT_PASSWORD=password123

# Common pattern
GIT_PASSWORD=Admin@123

# Personal info
GIT_PASSWORD=John@2024
```

## Advanced: Manual Testing

### Test URL Encoding

```python
from urllib.parse import quote

password = "MyP@ssw0rd#123!"
encoded = quote(password, safe='')
print(encoded)
# Output: MyP%40ssw0rd%23123%21
```

### Test Git Clone with Encoded Credentials

```bash
# Your password: MyP@ssw0rd#123!
# Manually encoded: MyP%40ssw0rd%23123%21

git clone https://user:MyP%40ssw0rd%23123%21@bitbucket.org/workspace/repo.git

# Should work if credentials are correct
```

## Summary

✅ **Enter passwords as-is** in `.env` file
✅ **All special characters** are automatically encoded
✅ **No manual encoding** needed
✅ **Works with all platforms**: Bitbucket, GitHub, GitLab, etc.
✅ **Secure**: Proper URL encoding prevents injection issues

The application handles all the complexity of URL encoding automatically, so you can focus on using your credentials without worrying about special character encoding!

## Related Documentation

- [README.md](README.md) - Main documentation
- [QUICKSTART.md](QUICKSTART.md) - Getting started
- [GITPYTHON_ANALYSIS_GUIDE.md](GITPYTHON_ANALYSIS_GUIDE.md) - Analysis guide
