# Step 10: CLI Interface

**Status**: Complete  
**Related Spec**: `specs/00-implementation-plan.md`

---

## Goals

1. Create Click-based CLI for command-line usage
2. Support all required parameters and options
3. Provide user-friendly help messages
4. Implement entry point in pyproject.toml
5. Support dry-run mode and statistics logging
6. Implement comprehensive unit tests

---

## Architecture Overview

The CLI serves as the user-facing interface to the scruby pipeline, translating command-line arguments into pipeline configuration and execution.

### Command Structure

```bash
scruby --src INPUT [OPTIONS]
```

---

## CLI Parameters

### Required Parameters

- `--src, -s PATH` - Input file or directory to process

### Optional Parameters

- `--out, -o PATH` - Output file or directory (stdout if not specified)
- `--config, -c PATH` - Configuration file path (default: config.yaml)
- `--reader TEXT` - Reader type to use (default: text_file)
- `--writer TEXT` - Writer type to use (default: auto-detect from --out)
- `--preprocessors TEXT` - Comma-separated list of preprocessors
- `--postprocessors TEXT` - Postprocessors to apply
- `--threshold FLOAT` - Confidence threshold override (0.0-1.0)
- `--verbose, -v` - Enable verbose output
- `--version` - Show version and exit

---

## Implementation Details

### Directory Structure

```
src/scruby/
├── __init__.py          # Version info
└── cli.py               # CLI implementation

tests/
└── test_cli.py          # CLI tests
```

---

## cli.py - CLI Implementation

```python
"""Command-line interface for scruby."""

import sys
from pathlib import Path
from typing import Optional

import click

from scruby.config import load_config
from scruby.pipeline import Pipeline, PipelineError


@click.command()
@click.option(
    "--src",
    "-s",
    "input_path",
    required=True,
    type=click.Path(exists=True),
    help="Input file or directory to process",
)
@click.option(
    "--out",
    "-o",
    "output_path",
    type=click.Path(),
    help="Output file or directory (stdout if not specified)",
)
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=True),
    default="config.yaml",
    help="Configuration file path",
)
@click.option(
    "--reader",
    default="text_file",
    help="Reader type to use",
)
@click.option(
    "--writer",
    help="Writer type to use (auto-detect if not specified)",
)
@click.option(
    "--preprocessors",
    help="Comma-separated list of preprocessors",
)
@click.option(
    "--postprocessors",
    help="Comma-separated list of postprocessors",
)
@click.option(
    "--threshold",
    type=float,
    help="Confidence threshold override (0.0-1.0)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.version_option(version="0.1.0", prog_name="scruby")
def main(
    input_path: str,
    output_path: Optional[str],
    config_path: str,
    reader: str,
    writer: Optional[str],
    preprocessors: Optional[str],
    postprocessors: Optional[str],
    threshold: Optional[float],
    verbose: bool,
) -> None:
    """
    Scruby - PII Redaction Tool for HIPAA Compliance.
    
    Redacts personally identifiable information (PII) from text documents
    using Microsoft Presidio and custom recognizers for HIPAA identifiers.
    """
    try:
        # Load configuration
        config = load_config(config_path)
        
        # Override threshold if specified
        if threshold is not None:
            if not 0.0 <= threshold <= 1.0:
                click.echo("Error: Threshold must be between 0.0 and 1.0", err=True)
                sys.exit(1)
            config["confidence_threshold"] = threshold
        
        # Auto-detect writer if not specified
        if writer is None:
            writer = "stdout" if output_path is None else "text_file"
        
        # Parse preprocessor/postprocessor lists
        preprocessor_list = (
            [p.strip() for p in preprocessors.split(",") if p.strip()]
            if preprocessors
            else None
        )
        postprocessor_list = (
            [p.strip() for p in postprocessors.split(",") if p.strip()]
            if postprocessors
            else None
        )
        
        if verbose:
            click.echo(f"Processing: {input_path}")
            click.echo(f"Output: {output_path or 'stdout'}")
            click.echo(f"Reader: {reader}")
            click.echo(f"Writer: {writer}")
            if preprocessor_list:
                click.echo(f"Preprocessors: {', '.join(preprocessor_list)}")
            if postprocessor_list:
                click.echo(f"Postprocessors: {', '.join(postprocessor_list)}")
        
        # Initialize and run pipeline
        pipeline = Pipeline(config=config)
        
        results = pipeline.process(
            input_path=input_path,
            output_path=output_path,
            reader_type=reader,
            writer_type=writer,
            preprocessors=preprocessor_list,
            postprocessors=postprocessor_list,
        )
        
        # Display results if verbose
        if verbose:
            total_entities = sum(
                len(doc.get("metadata", {}).get("redacted_entities", []))
                for doc in results
            )
            click.echo(f"\nProcessed {len(results)} document(s)")
            click.echo(f"Redacted {total_entities} PII entities")
        
        sys.exit(0)
        
    except PipelineError as e:
        click.echo(f"Pipeline error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## pyproject.toml Update

Add CLI entry point:

```toml
[project.scripts]
scruby = "scruby.cli:main"
```

---

## Unit Tests

### Test Coverage (`tests/test_cli.py`)

**Test Basic Functionality:**
1. `test_cli_help` - Verify help message displays
2. `test_cli_version` - Check version display
3. `test_cli_missing_src` - Error when --src not provided

**Test File Processing:**
4. `test_cli_single_file_to_stdout` - Process file to stdout
5. `test_cli_single_file_to_file` - Process file to file
6. `test_cli_directory` - Process directory

**Test Options:**
7. `test_cli_with_preprocessors` - Apply preprocessors
8. `test_cli_with_postprocessors` - Apply postprocessors
9. `test_cli_with_threshold` - Override threshold
10. `test_cli_invalid_threshold` - Reject invalid threshold

**Test Verbose Mode:**
11. `test_cli_verbose_output` - Verify verbose messages

**Test Error Handling:**
12. `test_cli_invalid_input_path` - Handle missing input
13. `test_cli_invalid_reader` - Handle unknown reader
14. `test_cli_pipeline_error` - Handle pipeline failures

---

## Usage Examples

### Basic Usage - Output to Stdout

```bash
scruby --src input.txt
```

### Process File to File

```bash
scruby --src sensitive.txt --out redacted.txt
```

### Process Directory

```bash
scruby --src input_dir/ --out output_dir/
```

### With Preprocessing and Postprocessing

```bash
scruby --src input.txt --out output.txt \
  --preprocessors whitespace_normalizer,text_cleaner \
  --postprocessors redaction_cleaner,format_preserver
```

### Override Confidence Threshold

```bash
scruby --src input.txt --threshold 0.8
```

### Custom Configuration

```bash
scruby --src input.txt --config custom_config.yaml
```

### Verbose Mode

```bash
scruby --src input.txt --out output.txt --verbose
```

---

## Success Criteria

- ✅ CLI entry point configured in pyproject.toml
- ✅ All parameters working correctly
- ✅ Help messages clear and informative
- ✅ Auto-detection of writer type working
- ✅ Verbose mode provides useful information
- ✅ Error handling robust
- ✅ All unit tests pass

---

## Next Step

After completing Step 10, proceed to:
**Step 11: Integration Testing** (`specs/11-integration-testing.md`)
