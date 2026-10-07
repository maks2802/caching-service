import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx
from pydantic import Field, HttpUrl, PositiveInt, model_validator
from pydantic_settings import BaseSettings


class CLISettings(BaseSettings):
    """Pydantic Settings model for sanitizing and validating input parameters."""

    host: HttpUrl = Field(default="http://localhost:8000")
    repeat: PositiveInt = Field(default=1)
    input_source: str | None = Field(default=None)
    json_data: str | None = Field(default=None)
    output_dest: str = Field(default="-")

    @model_validator(mode="after")
    def validate_inputs(self) -> "CLISettings":
        """Validates the logic for mutually exclusive data sources."""
        if not self.input_source and not self.json_data:
            raise ValueError("Must provide either --input (-i) or --json (-j).")
        if self.input_source and self.json_data:
            raise ValueError("Cannot provide both --input and --json.")
        return self


def parse_arguments() -> CLISettings:
    """
    Uses argparse to handle short/long flags and passes them
    to Pydantic for sanitization.
    """
    parser = argparse.ArgumentParser(
        description="CLI tool to test the Caching Service programmatically."
    )

    # Using only --host to avoid conflict with -h (help)
    parser.add_argument(
        "--host", type=str, default="http://localhost:8000", help="Base URL of the caching service"
    )
    parser.add_argument(
        "-r", "--repeat", type=int, default=1, help="Number of iterations to execute"
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        dest="input_source",
        help="Input file path or '-' for standard input",
    )
    parser.add_argument(
        "-j", "--json", type=str, dest="json_data", help="Input payload directly as JSON string"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="-",
        dest="output_dest",
        help="Output file path or '-' for standard output",
    )

    args = parser.parse_args()

    # Create a Pydantic object that automatically validates all types
    return CLISettings(**vars(args))


def load_input_payload(settings: CLISettings) -> dict[str, Any]:
    """Reads and validates the JSON payload structure."""
    raw_content = ""

    if settings.json_data:
        raw_content = settings.json_data
    elif settings.input_source == "-":
        raw_content = sys.stdin.read()
    elif settings.input_source:
        path = Path(settings.input_source)
        if not path.is_file():
            raise FileNotFoundError(f"Input file not found: {settings.input_source}")
        raw_content = path.read_text(encoding="utf-8")

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse input data as valid JSON: {exc}") from exc

    if not isinstance(data, dict) or "list_1" not in data or "list_2" not in data:
        raise ValueError(
            "Invalid payload format. Must be a JSON object with 'list_1' and 'list_2' arrays."
        )

    return data


def write_output(target: str, content: str) -> None:
    """Writes the result to a file or prints it to the terminal."""
    if target == "-":
        sys.stdout.write(f"{content}\n")
    else:
        Path(target).write_text(f"{content}\n", encoding="utf-8")


def run_cli() -> None:
    """Main entry point."""
    try:
        settings = parse_arguments()
        payload = load_input_payload(settings)
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)

    # Pydantic HttpUrl is converted to a string for httpx
    base_url = str(settings.host).rstrip("/")

    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        last_output = ""
        for iteration in range(1, settings.repeat + 1):
            try:
                # Send POST request
                post_res = client.post("/payload", json=payload)
                post_res.raise_for_status()
                payload_id = post_res.json().get("id")

                # Send GET request
                get_res = client.get(f"/payload/{payload_id}")
                get_res.raise_for_status()
                last_output = get_res.json().get("output", "")

            except httpx.HTTPError as exc:
                sys.stderr.write(f"HTTP error on iteration {iteration}: {exc}\n")
                sys.exit(1)

        write_output(settings.output_dest, last_output)


if __name__ == "__main__":
    run_cli()
