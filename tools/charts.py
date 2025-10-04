"""
Charts generator for metrics visualization.
Creates latency and throughput charts from CSV data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import typer
from pathlib import Path
from typing import Optional


app = typer.Typer(help="Metrics Charts Generator")


def load_metrics_data(csv_path: Path) -> pd.DataFrame:
    """Load metrics data from CSV file"""
    try:
        df = pd.read_csv(csv_path)
        
        # Validate required columns
        required_cols = ["ps_per_site", "avg_ms", "stdev_ms", "count_2min"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        return df
    except Exception as e:
        raise typer.BadParameter(f"Error loading CSV file: {e}")


def create_latency_chart(df: pd.DataFrame, output_path: Path):
    """Create latency vs PS chart"""
    # Group by ps_per_site and calculate averages
    latency_data = df.groupby('ps_per_site').agg({
        'avg_ms': 'mean',
        'stdev_ms': 'mean'
    }).reset_index()
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    
    # Plot with error bars
    plt.errorbar(
        latency_data['ps_per_site'],
        latency_data['avg_ms'],
        yerr=latency_data['stdev_ms'],
        marker='o',
        capsize=5,
        capthick=2,
        linewidth=2,
        markersize=8
    )
    
    plt.xlabel('PS per Site')
    plt.ylabel('Average Latency (ms)')
    plt.title('Average Latency vs PS per Site')
    plt.grid(True, alpha=0.3)
    
    # Set x-axis to show all PS values
    plt.xticks(latency_data['ps_per_site'])
    
    # Save with transparent background
    plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()


def create_throughput_chart(df: pd.DataFrame, output_path: Path):
    """Create throughput vs PS chart"""
    # Group by ps_per_site and calculate total throughput
    throughput_data = df.groupby('ps_per_site')['count_2min'].sum().reset_index()
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    
    # Plot bars
    plt.bar(
        throughput_data['ps_per_site'],
        throughput_data['count_2min'],
        alpha=0.7,
        edgecolor='black',
        linewidth=1
    )
    
    plt.xlabel('PS per Site')
    plt.ylabel('Total PRESTAR OK Count (2 min)')
    plt.title('Throughput vs PS per Site')
    plt.grid(True, alpha=0.3, axis='y')
    
    # Set x-axis to show all PS values
    plt.xticks(throughput_data['ps_per_site'])
    
    # Add value labels on bars
    for i, v in enumerate(throughput_data['count_2min']):
        plt.text(throughput_data['ps_per_site'].iloc[i], v + 0.5, 
                str(v), ha='center', va='bottom')
    
    # Save with transparent background
    plt.savefig(output_path, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()


def create_comparison_chart(df: pd.DataFrame, output_path: Path):
    """Create comparison chart between serial and threaded modes"""
    if 'mode' not in df.columns:
        return
    
    # Group by ps_per_site and mode
    comparison_data = df.groupby(['ps_per_site', 'mode']).agg({
        'avg_ms': 'mean',
        'count_2min': 'sum'
    }).reset_index()
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Latency comparison
    for mode in comparison_data['mode'].unique():
        mode_data = comparison_data[comparison_data['mode'] == mode]
        ax1.plot(mode_data['ps_per_site'], mode_data['avg_ms'], 
                marker='o', label=f'{mode.capitalize()} Mode', linewidth=2, markersize=8)
    
    ax1.set_xlabel('PS per Site')
    ax1.set_ylabel('Average Latency (ms)')
    ax1.set_title('Latency Comparison: Serial vs Threaded')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Throughput comparison
    for mode in comparison_data['mode'].unique():
        mode_data = comparison_data[comparison_data['mode'] == mode]
        ax2.plot(mode_data['ps_per_site'], mode_data['count_2min'], 
                marker='s', label=f'{mode.capitalize()} Mode', linewidth=2, markersize=8)
    
    ax2.set_xlabel('PS per Site')
    ax2.set_ylabel('Total PRESTAR OK Count (2 min)')
    ax2.set_title('Throughput Comparison: Serial vs Threaded')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save with transparent background
    plt.savefig(output_path, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()


@app.command()
def main(
    csv: Path = typer.Option(
        "metrics/results.csv", "--csv", "-c",
        help="Path to metrics CSV file"
    ),
    outdir: Path = typer.Option(
        "metrics/", "--outdir", "-o",
        help="Output directory for charts"
    ),
    comparison: bool = typer.Option(
        False, "--comparison", "-cmp",
        help="Create comparison chart between modes"
    )
):
    """
    Generate charts from metrics CSV data.
    
    Creates latency and throughput charts showing performance
    characteristics of the distributed library system.
    """
    
    # Validate input file
    if not csv.exists():
        typer.echo(f"Error: CSV file {csv} not found", err=True)
        raise typer.Exit(1)
    
    # Create output directory
    outdir.mkdir(parents=True, exist_ok=True)
    
    typer.echo(f"Loading metrics from {csv}...")
    
    try:
        # Load data
        df = load_metrics_data(csv)
        typer.echo(f"Loaded {len(df)} data points")
        
        # Show data summary
        typer.echo(f"PS per site values: {sorted(df['ps_per_site'].unique())}")
        if 'mode' in df.columns:
            typer.echo(f"Modes: {df['mode'].unique()}")
        
        # Generate charts
        typer.echo("\nGenerating charts...")
        
        # Latency chart
        latency_path = outdir / "latency_vs_ps.png"
        create_latency_chart(df, latency_path)
        typer.echo(f"  Created latency chart: {latency_path}")
        
        # Throughput chart
        throughput_path = outdir / "throughput_vs_ps.png"
        create_throughput_chart(df, throughput_path)
        typer.echo(f"  Created throughput chart: {throughput_path}")
        
        # Comparison chart (if requested and data available)
        if comparison and 'mode' in df.columns:
            comparison_path = outdir / "comparison_modes.png"
            create_comparison_chart(df, comparison_path)
            typer.echo(f"  Created comparison chart: {comparison_path}")
        
        typer.echo(f"\nCharts generated successfully in {outdir}")
        
    except Exception as e:
        typer.echo(f"Error generating charts: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
