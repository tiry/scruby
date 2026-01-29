"""Command-line interface for scruby."""

import sys
from pathlib import Path
from typing import Optional

import click

from scruby import __version__
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
@click.version_option(version=__version__, prog_name="scruby")
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
            # Update the config object
            config.default_confidence_threshold = threshold
        
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
                doc.get("metadata", {}).get("redacted_entities", 0)
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
