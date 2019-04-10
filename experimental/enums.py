class CWLTypes:
    """
    Enum class for CWL.v1 inputs and outputs
    """

    File = ["File", "File?"]
    Int = ["int", "int?"]
    String = ["string", "string?"]
    Float = ["float", "float?"]
    Bool = ["boolean", "boolean?"]
    Map = ["map", "map?"]
    Array = [
        "File[]",
        "File[]?",
        "int[]",
        "int[]?",
        "string[]",
        "string[]?",
        "float[]",
        "float[]?",
        "boolean[]",
        "boolean[]?",
        "map[]",
        "map[]?",
        {"items": "File", "type": "array"},
        [{"items": "File", "type": "array"}],
    ]


class CWLDraft2Types:
    """
    Enum class for CWL.draft2 inputs and outputs
    """

    File = ["File", "File?"]
    Int = ["int", "int?"]
    String = ["string", "string?"]
    Float = ["float", "float?"]
    Bool = ["boolean", "boolean?"]
    Map = ["map", "map?"]
    Array = [
        {"items": "File", "type": "array"},
        [{"items": "File", "type": "array"}],
        {"items": "string", "type": "array"},
        [{"items": "string", "type": "array"}],
        {"items": "int", "type": "array"},
        [{"items": "int", "type": "array"}],
        {"items": "float", "type": "array"},
        [{"items": "float", "type": "array"}],
        {"items": "boolean", "type": "array"},
        [{"items": "boolean", "type": "array"}],
    ]
