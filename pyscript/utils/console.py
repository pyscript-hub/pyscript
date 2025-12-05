from rich.console import Console as RichConsole
from typing import Optional


# rich.console.Console instance
console = RichConsole()


class Console:
    """
    Wrapper class to provide rich console functionality.
    """

    @classmethod
    def print(cls, *args, **kwargs):
        """
        Basic print method. Wrapper around Console.print().
        """
        console.print(*args, **kwargs)

    @classmethod
    def print_error(cls, msg: str, desc: Optional[str] = None) -> None:
        """
        Display an error message with the form: "❌ [red]Error:[/red] {msg}." + [" {desc}"]
        """

        string = f"❌ [red]Error:[/red] {msg}." + ((" " + desc) if desc else "")
        cls.print(string)

    @classmethod
    def print_warning(cls, msg: str, desc: Optional[str] = None) -> None:
        """
        Display a warning message with the form: "⚠️  [yellow]Warning:[/yellow] {msg}." + [" {desc}"]
        """

        string = f"⚠️  [yellow]Warning:[/yellow] {msg}." + ((" " + desc) if desc else "")
        cls.print(string)

    @classmethod
    def print_success(cls, msg: str) -> None:
        """
        Display a success message with the form: "✅ {msg}"
        """

        string = f"✅ {msg}"
        cls.print(string)

    @classmethod
    def input(cls, prompt: str) -> str:
        """
        Get input from the console.

        Arguments:
            prompt: the prompt to be printed.

        Returns:
            The input from the console.
        """

        return console.input(prompt)

    @classmethod
    def confirm_action(cls, prompt: str, default: bool = False) -> bool:
        """
        Method to ask user to confirm a yes/no question.

        Arguments:
            prompt: the prompt to be printed.
            default: the default answer.

        Returns:
            A boolean indicating the user confirmation.
        """

        choice = "Y/n" if default else "y/N"
        res = Console.input(f"️❗ {prompt} ({choice}): ").lower().strip()
        if not res:
            return default
        return res == 'y'