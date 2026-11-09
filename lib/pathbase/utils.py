import string
import re


# Patterns for tokens that need more than "anything but a separator".
# frame_rate takes decimals so they can be floored, as get_frame_rate does.
FORMAT_TOKEN_PATTERNS = {"frame_rate": r"\d+(?:\.\d+)?"}


def parse_format(format_value, write_format, token_patterns=None):
    """Split a {format} value back into its original tokens.

    The reverse of how construct_write_path builds fields["format"]. Works
    with any tokens and separators in the pattern, e.g. "{a}-{b}_{c}".

    A token's value can't contain any of the pattern's separator characters,
    so it can't spill into the next token. Tokens in FORMAT_TOKEN_PATTERNS
    use their own pattern, and token_patterns can add to or override those.

    A {frame_rate} value is floored to a whole number, e.g. "23.976" gives
    "23", to match get_frame_rate.

    Args:
        format_value (str): The {format} part of a path, e.g.
            "foo-bar-spam".
        write_format (str): Format pattern to parse with.
        token_patterns (dict, optional): Token name mapped to a regex its
            value must match.

    Returns:
        dict: Token name mapped to its value as it appears in the path.

    Raises:
        ValueError: If format_value doesn't fit write_format.
    """

    token_patterns = {**FORMAT_TOKEN_PATTERNS, **(token_patterns or {})}
    parts = list(string.Formatter().parse(write_format))

    # A token matches anything but "/" and the characters between tokens
    separators = set("/".join(literal for literal, *_ in parts)) | {"/"}
    default = "[^" + "".join(re.escape(c) for c in sorted(separators)) + "]+"

    regex = ""
    for literal, field, _spec, _conv in parts:
        regex += re.escape(literal)
        if field is not None:
            regex += f"(?P<{field}>{token_patterns.get(field, default)})"

    match = re.fullmatch(regex, format_value)
    if not match:
        raise ValueError(
            f"'{format_value}' doesn't fit format '{write_format}'."
        )

    tokens = match.groupdict()

    return tokens

