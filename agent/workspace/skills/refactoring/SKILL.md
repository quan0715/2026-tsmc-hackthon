## General Refactoring Patterns

### Pattern: Nested Ifs → Guard Clauses

**Before:**
```python
def process_user(user):
    if user is not None:
        if user.is_active:
            if user.has_permission('write'):
                return user.update_profile()
            else:
                return None
        else:
            return None
    else:
        return None
```

**After:**
```python
def process_user(user):
    if user is None:
        return None
    if not user.is_active:
        return None
    if not user.has_permission('write'):
        return None
    return user.update_profile()
```

### Pattern: Long Function → Extract Method

**Before:**
```python
def generate_report(data):
    # Validation
    if not data:
        raise ValueError("No data")
    # Calculation
    total = sum(item['value'] for item in data)
    average = total / len(data)
    # Formatting
    return f"Total: {total}, Average: {average:.2f}"
```

**After:**
```python
def generate_report(data):
    _validate_data(data)
    stats = _calculate_statistics(data)
    return _format_report(stats)

def _validate_data(data):
    if not data:
        raise ValueError("No data")

def _calculate_statistics(data):
    values = [item['value'] for item in data]
    return {'total': sum(values), 'average': sum(values) / len(values)}

def _format_report(stats):
    return f"Total: {stats['total']}, Average: {stats['average']:.2f}"
```

---

## Migration Principles

### Semantic Correctness
- **CRITICAL**: Migrated code must produce identical outputs for all inputs
- Preserve error handling behavior
- Maintain side effects (file I/O, DB calls)

### Test Coverage
- **Project 1:** Aim for 100% line coverage (maximizes 30% scoring weight)
- **Project 3:** All RAW SQL must be covered by tests (30% scoring weight)
- Generate edge case tests (zero, null, boundary values)

### Comment Handling
- Preserve meaningful comments explaining "why"
- Update comments if code structure changes
- When migrating languages, translate comments to target language

### Formatting Standards
- **Python:** PEP 8 (4 spaces, snake_case)
- **Go:** gofmt (tabs, CamelCase)
- **TypeScript:** Prettier (2 spaces, camelCase)
