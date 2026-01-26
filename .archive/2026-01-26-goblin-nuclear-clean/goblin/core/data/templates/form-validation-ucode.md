---
title: Form Validation
version: 2.0.0
author: uDOS
created: 2026-01-06
tags: [form, validation, input, template]
description: Input validation patterns with error handling for user registration
permissions:
  execute: true
  save_state: false
variables:
  username: ""
  email: ""
  password: ""
  age: 0
---

# Form Validation Template

Demonstrates input validation patterns with various validation rules and error handling.

---

## Introduction

Display the form header.

```upy
PRINT "=========================================="
PRINT "  User Registration Form"
PRINT "=========================================="
PRINT ""
```

---

## Username Validation

Validate username length (3-20 characters).

```upy
LABEL USERNAME_INPUT

username = INPUT "Enter username (3-20 characters):"
username_length = LEN(username)

IF username_length < 3:
    PRINT "❌ Username too short! (minimum 3 characters)"
    GOTO USERNAME_INPUT

IF username_length > 20:
    PRINT "❌ Username too long! (maximum 20 characters)"
    GOTO USERNAME_INPUT

# Check for valid characters (alphanumeric and underscore)
valid_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
FOR char IN username:
    IF char NOT IN valid_chars:
        PRINT "❌ Username contains invalid characters!"
        PRINT "   Use only letters, numbers, and underscores."
        GOTO USERNAME_INPUT

PRINT "✅ Username accepted"
PRINT ""
```

---

## Email Validation

Validate email format (contains @ and domain).

```upy
LABEL EMAIL_INPUT

email = INPUT "Enter email address:"

# Check for @ symbol
IF "@" NOT IN email:
    PRINT "❌ Invalid email: missing @ symbol"
    GOTO EMAIL_INPUT

# Check for domain part
parts = email.split("@")
IF LEN(parts) != 2:
    PRINT "❌ Invalid email format"
    GOTO EMAIL_INPUT

local_part = parts[0]
domain = parts[1]

IF LEN(local_part) == 0:
    PRINT "❌ Invalid email: empty local part"
    GOTO EMAIL_INPUT

IF "." NOT IN domain:
    PRINT "❌ Invalid email: domain must contain a dot"
    GOTO EMAIL_INPUT

IF domain.startswith(".") OR domain.endswith("."):
    PRINT "❌ Invalid email: malformed domain"
    GOTO EMAIL_INPUT

PRINT "✅ Email accepted"
PRINT ""
```

---

## Password Validation

Validate password strength (minimum 8 characters, complexity rules).

```upy
LABEL PASSWORD_INPUT

password = INPUT "Enter password (min 8 characters):"
password_length = LEN(password)

IF password_length < 8:
    PRINT "❌ Password too short! (minimum 8 characters)"
    GOTO PASSWORD_INPUT

# Check for complexity (at least one letter and one number)
has_letter = False
has_number = False
letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
numbers = "0123456789"

FOR char IN password:
    IF char IN letters:
        has_letter = True
    IF char IN numbers:
        has_number = True

IF NOT has_letter OR NOT has_number:
    PRINT "❌ Password must contain letters and numbers"
    GOTO PASSWORD_INPUT

PRINT "✅ Password accepted"
PRINT ""
```

---

## Password Confirmation

Confirm password matches.

```upy
LABEL PASSWORD_CONFIRM

password_confirm = INPUT "Confirm password:"

IF password != password_confirm:
    PRINT "❌ Passwords do not match!"
    GOTO PASSWORD_CONFIRM

PRINT "✅ Password confirmed"
PRINT ""
```

---

## Age Validation

Validate age (must be 13-120).

```upy
LABEL AGE_INPUT

age_input = INPUT "Enter age (must be 13 or older):"

# Try to convert to integer
age = INT(age_input)

IF age < 13:
    PRINT "❌ You must be 13 or older to register!"
    GOTO AGE_INPUT

IF age > 120:
    PRINT "❌ Please enter a valid age!"
    GOTO AGE_INPUT

PRINT "✅ Age accepted"
PRINT ""
```

---

## Registration Summary

Display the completed registration.

```upy
PRINT "=========================================="
PRINT "  Registration Summary"
PRINT "=========================================="
PRINT ""
PRINT "Username: " + username
PRINT "Email:    " + email
PRINT "Age:      " + str(age)
PRINT ""
PRINT "✅ Registration complete!"

# Award XP for completing registration
XP + 50

END
```

---

## Notes

This template demonstrates:

- **Input Validation**: Length, format, and content checks
- **Error Messages**: Clear feedback with retry loops
- **String Operations**: split(), IN operator, iteration
- **Type Conversion**: INT() for numeric input
- **Complexity Rules**: Multi-criteria validation

### Validation Patterns

| Field | Rules |
|-------|-------|
| Username | 3-20 chars, alphanumeric + underscore |
| Email | Contains @, valid domain with dot |
| Password | 8+ chars, letters and numbers |
| Age | Integer 13-120 |

### Customization Ideas

1. Add phone number validation
2. Add postal code validation
3. Add real-time validation feedback
4. Add password strength meter
5. Add terms of service checkbox
