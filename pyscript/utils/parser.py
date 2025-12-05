def parse_script_name(script_name: str) -> str:
    """
    Parse the script name replacing blank characters with dashes.

    Arguments:
        script_name: name of the script to be parsed

    Returns:
        The parsed script name
    """

    return script_name.replace(" ", "-")