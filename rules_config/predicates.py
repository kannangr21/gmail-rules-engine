PREDICATES = {
    "contains": lambda field, value: value.lower() in (field or "").lower(),
    "does_not_contain": lambda field, value: value.lower() not in (field or "").lower(),
    "equals": lambda field, value: (field or "").lower() == value.lower(),
    "does_not_equal": lambda field, value: (field or "").lower() != value.lower(),
    "starts_with": lambda field, value: (field or "").lower().startswith(value.lower()),
    "ends_with": lambda field, value: (field or "").lower().endswith(value.lower())
}
