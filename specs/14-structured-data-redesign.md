# Structured Data Architecture Redesign

## Problem Statement

Current implementation has a fundamental flaw in how it handles structured data:

**Current (Broken) Approach:**
1. `field_selector` concatenates selected fields into single "content" string with separators
2. Redactor processes the concatenated string
3. `dict_merger` tries to split redacted string back using separators
4. **FAILS** because entity lengths change during redaction, breaking boundary positions

**Test Results Showing the Bug:**
```
Name: <PERSON:7e3e          # Incomplete!
Email: 29> 12/25            # Fragment from previous field!
Phone: SS:156a3f7617d       # Part of SSN tag!
```

- 920 entities detected by Presidio ✅
- 99 fragmented field values ❌

## Correct Architecture

### 1. field_selector Preprocessor
**Purpose:** Select which fields to redact

**Input:**
```python
{
    "content": None,
    "metadata": {
        "original_data": {
            "ID": "1",
            "Name": "John Doe",
            "Email": "john@example.com",
            "SSN": "123-45-6789",
            "Phone": "555-1234",
            ...10 fields total
        }
    }
}
```

**Configuration:**
```yaml
field_selector:
  fields: ["Name", "Email", "SSN"]  # Only these 3 get redacted
```

**Output:**
```python
{
    "content": None,  # NOT USED for structured data!
    "metadata": {
        "original_data": {... all 10 fields ...},
        "selected_for_redaction": {
            "Name": "John Doe",
            "Email": "john@example.com", 
            "SSN": "123-45-6789"
        },
        "selected_fields": ["Name", "Email", "SSN"]
    }
}
```

### 2. Pipeline/Redactor Processing
**For each field in `selected_for_redaction`:**
```python
for field, value in selected_for_redaction.items():
    redacted_value = redactor.redact_text(value)
    redacted_data[field] = redacted_value
```

**Result:**
```python
{
    "metadata": {
        "original_data": {...},
        "redacted_fields": {
            "Name": "<PERSON:abc123>",
            "Email": "<EMAIL:def456>",
            "SSN": "<US_SSN:ghi789>"
        }
    }
}
```

### 3. dict_merger Postprocessor
**Purpose:** Reconstruct full dictionary

**Logic:**
```python
# Start with original data
output_dict = original_data.copy()

# Replace redacted fields
for field in selected_fields:
    if field in redacted_fields:
        output_dict[field] = redacted_fields[field]

# Result: 7 unselected fields (unchanged) + 3 redacted fields
```

**Output:**
```python
{
    "content": None,
    "metadata": {
        "redacted_data": {
            "ID": "1",              # Preserved
            "Name": "<PERSON:abc>",  # Redacted
            "Email": "<EMAIL:def>",  # Redacted  
            "SSN": "<US_SSN:ghi>",   # Redacted
            "Phone": "555-1234",     # Preserved
            ...  # All 10 fields present
        }
    }
}
```

## Implementation Changes Required

### 1. field_selector.py
- Remove content concatenation logic
- Remove field_boundaries tracking
- Simply extract selected fields to `selected_for_redaction` metadata

### 2. Pipeline (structured data path)
- Detect if `selected_for_redaction` exists in metadata
- If yes: iterate through each field, redact individually
- Store results in `redacted_fields` metadata
- Skip normal "content" redaction

### 3. dict_merger.py
- Remove separator splitting logic
- Simply merge: `preserved fields + redacted fields`
- Store final dict in `redacted_data` metadata

### 4. Writers
- Read from `metadata['redacted_data']` instead of trying to parse content

## Benefits

1. ✅ Each field redacted independently (no boundary issues)
2. ✅ Cleaner architecture (no string concatenation hack)
3. ✅ Entity count matches redaction count
4. ✅ Proper field-level granularity
5. ✅ Easier to maintain and test

## Testing

After redesign, Mendeley test should show:
- 920 entities detected
- 920 fields properly redacted (not 99 fragments)
- Each field contains complete `<ENTITY_TYPE:hash>` values

## Priority

**HIGH** - Current implementation is broken and produces incorrect/corrupted output for structured data.
