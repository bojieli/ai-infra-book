# Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import datetime
import glob
import json
import os
import statistics
import sys
from collections import defaultdict

from rich.box import SIMPLE
from rich.console import Console
from rich.table import Table
from rich.text import Text
from tensorboard.backend.event_processing import event_accumulator

# By default TB tries to be smart about what to load in memory to avoid OOM
# Since we expect every step to be there when we do our comparisons, we explicitly
# set the size guidance to 0 so that we load everything.
SIZE_GUIDANCE = {
    event_accumulator.TENSORS: 0,
    event_accumulator.SCALARS: 0,
}

console = Console()
error_console = Console(stderr=True)


def merge_tb_logs_to_json(
    log_dir, output_path, error_on_conflicts=False, required_tag_prefix=None
):
    """Merge multiple TensorBoard event files into a single JSON file.

    Arguments:
        log_dir: Path to directory containing TensorBoard event files (searched recursively)
        output_path: Path to save the output JSON file
        error_on_conflicts: If True, raise an error if conflicting values are found for the same step
        required_tag_prefix: If set, require at least one TensorBoard tag in any
            plugin category to start with this prefix

    Raises:
        ValueError: If conflicting values are found for the same step and
            error_on_conflicts is True, or if required_tag_prefix is not found
    """
    # Find all event files recursively
    files = glob.glob(f"{log_dir}/**/events*tfevents*", recursive=True)
    files.sort(key=lambda x: os.path.getmtime(x))

    if not files:
        raise FileNotFoundError(f"No TensorBoard event files found under {log_dir}")

    # Display found files in a table
    file_table = Table(title="Found TensorBoard Event Files", show_header=True)
    file_table.add_column("Index", style="dim")
    file_table.add_column("Path", style="green")
    file_table.add_column("Last Modified", style="cyan")

    # Keep a map of file index to path for conflict reporting
    file_index_map = {}
    for i, f in enumerate(files, 1):
        file_index_map[f] = i
        modified_time = os.path.getmtime(f)
        formatted_time = datetime.datetime.fromtimestamp(modified_time).strftime(
            "%Y/%m/%d %H:%M:%S"
        )
        file_table.add_row(str(i), f, formatted_time)

    console.print(file_table)

    # {metric_name: {step: (value, source_file)}}
    merged_data = defaultdict(dict)
    tensorboard_tags = set()

    console.print("[bold green]Processing event files...[/bold green]")

    for event_file in files:
        console.print(f"Processing {os.path.basename(event_file)}")

        ea = event_accumulator.EventAccumulator(event_file, size_guidance=SIZE_GUIDANCE)
        ea.Reload()

        for tags in ea.Tags().values():
            if isinstance(tags, list):
                tensorboard_tags.update(tags)

        for metric_name in ea.scalars.Keys():
            for scalar in ea.Scalars(metric_name):
                step, value = scalar.step, scalar.value

                # Check for conflicts - raise error only if error_on_conflicts is True
                if step in merged_data[metric_name]:
                    existing_value, existing_file = merged_data[metric_name][step]

                    # Only consider it a conflict if the values are different
                    if existing_value != value:
                        if error_on_conflicts:
                            # Immediate error if we choose to error on conflicts
                            raise ValueError(
                                f"Conflict detected for metric '{metric_name}' at step {step}:\n"
                                f"  File #{file_index_map[existing_file]}: {existing_file} has value {existing_value}\n"
                                f"  File #{file_index_map[event_file]}: {event_file} has value {value}\n"
                                f"Re-run without --error-on-conflicts to merge with the latest value."
                            )

                # Add or override the value
                merged_data[metric_name][step] = (value, event_file)

    if required_tag_prefix is not None and not any(
        tag.startswith(required_tag_prefix) for tag in tensorboard_tags
    ):
        raise ValueError(
            f"No TensorBoard tag starts with '{required_tag_prefix}' under {log_dir}"
        )

    # Convert defaultdict to regular dict and sort the steps
    output_data = {}
    for metric_name in sorted(merged_data.keys()):
        output_data[metric_name] = {
            str(step): merged_data[metric_name][step][
                0
            ]  # Just keep the value, not the source file
            for step in sorted(merged_data[metric_name].keys())
        }

    # Create summary table header
    console.print("\n[bold cyan]Metrics Summary:[/bold cyan]")

    # Display summary for each metric using tables for better alignment
    for metric, steps_data in sorted(output_data.items()):
        if not steps_data:
            console.print(f"[bold magenta]{metric}[/bold magenta] - No data")
            continue

        # Get steps and values as sorted lists
        steps = sorted([int(step) for step in steps_data.keys()])
        values = [steps_data[str(step)] for step in steps]

        # Calculate statistics
        min_val = min(values)
        max_val = max(values)
        avg_val = statistics.mean(values)

        # Create metric header with better highlighting
        metric_text = Text()
        metric_text.append("🔹 ", style="bold blue")
        metric_text.append(f"{metric}", style="bold magenta")
        metric_text.append(f" - {len(steps)} steps", style="green")
        console.print(metric_text)

        # Create statistics panel
        stats_text = Text()
        stats_text.append("Min: ", style="dim")
        stats_text.append(f"{min_val:.6g}", style="red")
        stats_text.append("   Max: ", style="dim")
        stats_text.append(f"{max_val:.6g}", style="green")
        stats_text.append("   Avg: ", style="dim")
        stats_text.append(f"{avg_val:.6g}", style="yellow")
        console.print(stats_text)

        # Create value table
        value_table = Table(show_header=True, header_style="bold", box=SIMPLE)

        # Determine what to display
        if len(steps) <= 6:
            # Show all steps
            display_indices = list(range(len(steps)))
            for i in display_indices:
                value_table.add_column(f"Step {steps[i]}")
        else:
            # Show first 3 and last 3
            display_indices = [0, 1, 2, len(steps) - 3, len(steps) - 2, len(steps) - 1]
            value_table.add_column(f"Step {steps[0]}")
            value_table.add_column(f"Step {steps[1]}")
            value_table.add_column(f"Step {steps[2]}")
            value_table.add_column("...")
            value_table.add_column(f"Step {steps[-3]}")
            value_table.add_column(f"Step {steps[-2]}")
            value_table.add_column(f"Step {steps[-1]}")

        # Add value row
        if len(steps) <= 6:
            value_table.add_row(*[f"{values[i]:.6g}" for i in display_indices])
        else:
            value_table.add_row(
                f"{values[0]:.6g}",
                f"{values[1]:.6g}",
                f"{values[2]:.6g}",
                "...",
                f"{values[-3]:.6g}",
                f"{values[-2]:.6g}",
                f"{values[-1]:.6g}",
            )

        console.print(value_table)
        console.print()

    # Write the merged data to JSON file
    if output_path:
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        console.print(
            f"[bold green]✓ Merged data written to {output_path}[/bold green]"
        )
    else:
        console.print(
            "[bold red]✓ To save the merged data, use --output_path[/bold red]"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge TensorBoard event files into a single JSON file"
    )
    parser.add_argument(
        "log_dir", type=str, help="Directory containing TensorBoard event files"
    )
    parser.add_argument(
        "--output_path",
        required=False,
        default=None,
        type=str,
        help="Path to save the output JSON file",
    )
    parser.add_argument(
        "--error-on-conflicts",
        action="store_true",
        help="Error out when conflicting values are found for the same step",
    )
    parser.add_argument(
        "--require-tag-prefix",
        default=None,
        help="Require a TensorBoard tag in any plugin category with this prefix",
    )

    args = parser.parse_args()

    try:
        merge_tb_logs_to_json(
            args.log_dir,
            args.output_path,
            args.error_on_conflicts,
            args.require_tag_prefix,
        )
    except Exception as e:
        error_console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)
