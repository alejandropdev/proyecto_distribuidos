"""
Load generator script that spawns multiple PS clients and measures performance.
Generates metrics CSV with latency and throughput data.
"""

import csv
import json
import multiprocessing
import subprocess
import sys
import time
import typer
from pathlib import Path
from typing import List, Dict, Any, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from common.time_utils import now_ms
from common.env import MEASUREMENT_WINDOW_SEC


app = typer.Typer(help="PS Load Generator")


class PSWorker:
    """Worker process for PS client"""
    
    def __init__(
        self, 
        site: str, 
        gc_endpoint: str, 
        requests_file: Path,
        duration_sec: int
    ):
        self.site = site
        self.gc_endpoint = gc_endpoint
        self.requests_file = requests_file
        self.duration_sec = duration_sec
    
    def run(self) -> Dict[str, Any]:
        """Run PS client and return metrics"""
        try:
            # Import here to avoid multiprocessing issues
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent))
            
            from ps.client import PSClient, load_requests_from_file
            from common.models import ClientRequest
            
            # Load requests
            request_data = load_requests_from_file(self.requests_file)
            
            # Create client
            client = PSClient(self.gc_endpoint, pretty=False)
            
            # Metrics collection
            prestar_latencies = []
            prestar_count = 0
            prestar_ok_count = 0
            total_requests = 0
            
            start_time = now_ms()
            end_time = start_time + (self.duration_sec * 1000)
            
            try:
                for req_data in request_data:
                    # Check if we've exceeded duration
                    if now_ms() >= end_time:
                        break
                    
                    # Create request
                    request = ClientRequest(
                        sedeId=self.site,
                        userId=req_data["userId"],
                        op=req_data["op"],
                        libroCodigo=req_data["libroCodigo"],
                        timestamp=now_ms()
                    )
                    
                    # Send request
                    response, latency = client.send_request(request)
                    total_requests += 1
                    
                    # Collect PRESTAR metrics
                    if request.op == "PRESTAR":
                        prestar_count += 1
                        if latency is not None:
                            prestar_latencies.append(latency)
                        if response.status == "OK":
                            prestar_ok_count += 1
                    
                    # Small delay between requests
                    time.sleep(0.01)  # 10ms delay
                    
            finally:
                client.close()
            
            # Calculate metrics
            avg_latency = 0
            stdev_latency = 0
            
            if prestar_latencies:
                avg_latency = sum(prestar_latencies) / len(prestar_latencies)
                if len(prestar_latencies) > 1:
                    variance = sum((x - avg_latency) ** 2 for x in prestar_latencies) / (len(prestar_latencies) - 1)
                    stdev_latency = variance ** 0.5
            
            return {
                "site": self.site,
                "total_requests": total_requests,
                "prestar_count": prestar_count,
                "prestar_ok_count": prestar_ok_count,
                "avg_latency": avg_latency,
                "stdev_latency": stdev_latency,
                "latencies": prestar_latencies
            }
            
        except Exception as e:
            return {
                "site": self.site,
                "error": str(e),
                "total_requests": 0,
                "prestar_count": 0,
                "prestar_ok_count": 0,
                "avg_latency": 0,
                "stdev_latency": 0,
                "latencies": []
            }


def run_ps_worker(args: Tuple[str, str, Path, int]) -> Dict[str, Any]:
    """Wrapper function for multiprocessing"""
    site, gc_endpoint, requests_file, duration_sec = args
    worker = PSWorker(site, gc_endpoint, requests_file, duration_sec)
    return worker.run()


@app.command()
def main(
    ps_per_site: int = typer.Option(
        4, "--ps-per-site", "-n",
        help="Number of PS processes per site"
    ),
    sites: str = typer.Option(
        "A,B", "--sites", "-s",
        help="Comma-separated list of sites (e.g., A,B)"
    ),
    duration_sec: int = typer.Option(
        MEASUREMENT_WINDOW_SEC, "--duration-sec", "-d",
        help="Measurement duration in seconds"
    ),
    file: Path = typer.Option(
        "data/ejemplos/peticiones_sample.txt", "--file", "-f",
        help="Path to peticiones.txt file"
    ),
    gc: str = typer.Option(
        "tcp://127.0.0.1:5555", "--gc", "-g",
        help="GC endpoint"
    ),
    mode: str = typer.Option(
        "serial", "--mode", "-m",
        help="GC mode (serial or threaded)"
    ),
    out: Path = typer.Option(
        "metrics/results.csv", "--out", "-o",
        help="Output CSV file"
    )
):
    """
    Spawn multiple PS clients and measure performance.
    
    Launches N PS processes per site, runs them for the specified duration,
    and generates metrics CSV with latency and throughput data.
    """
    
    # Parse sites
    site_list = [s.strip() for s in sites.split(",")]
    if not site_list:
        typer.echo("Error: No sites specified", err=True)
        raise typer.Exit(1)
    
    # Validate file exists
    if not file.exists():
        typer.echo(f"Error: File {file} not found", err=True)
        raise typer.Exit(1)
    
    # Create output directory
    out.parent.mkdir(parents=True, exist_ok=True)
    
    typer.echo(f"Starting load test:")
    typer.echo(f"  Sites: {site_list}")
    typer.echo(f"  PS per site: {ps_per_site}")
    typer.echo(f"  Duration: {duration_sec}s")
    typer.echo(f"  GC endpoint: {gc}")
    typer.echo(f"  GC mode: {mode}")
    typer.echo(f"  Output: {out}")
    
    # Prepare worker arguments
    worker_args = []
    for site in site_list:
        for i in range(ps_per_site):
            worker_args.append((site, gc, file, duration_sec))
    
    typer.echo(f"\nLaunching {len(worker_args)} PS processes...")
    
    # Run workers
    start_time = now_ms()
    results = []
    
    try:
        with ProcessPoolExecutor(max_workers=len(worker_args)) as executor:
            # Submit all workers
            future_to_args = {
                executor.submit(run_ps_worker, args): args 
                for args in worker_args
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_args):
                args = future_to_args[future]
                site, _, _, _ = args
                
                try:
                    result = future.result()
                    results.append(result)
                    typer.echo(f"  PS from site {site} completed")
                except Exception as e:
                    typer.echo(f"  PS from site {site} failed: {e}")
                    results.append({
                        "site": site,
                        "error": str(e),
                        "total_requests": 0,
                        "prestar_count": 0,
                        "prestar_ok_count": 0,
                        "avg_latency": 0,
                        "stdev_latency": 0,
                        "latencies": []
                    })
    
    except KeyboardInterrupt:
        typer.echo("\nLoad test interrupted by user")
        return
    
    end_time = now_ms()
    total_duration_ms = end_time - start_time
    
    typer.echo(f"\nLoad test completed in {total_duration_ms/1000:.2f}s")
    
    # Aggregate results
    typer.echo("\nAggregating results...")
    
    # Group results by site
    site_results = {}
    for result in results:
        site = result["site"]
        if site not in site_results:
            site_results[site] = []
        site_results[site].append(result)
    
    # Calculate aggregated metrics
    aggregated_results = []
    
    for site, site_result_list in site_results.items():
        # Aggregate latencies
        all_latencies = []
        total_prestar_ok = 0
        
        for result in site_result_list:
            all_latencies.extend(result.get("latencies", []))
            total_prestar_ok += result.get("prestar_ok_count", 0)
        
        # Calculate metrics
        avg_latency = 0
        stdev_latency = 0
        
        if all_latencies:
            avg_latency = sum(all_latencies) / len(all_latencies)
            if len(all_latencies) > 1:
                variance = sum((x - avg_latency) ** 2 for x in all_latencies) / (len(all_latencies) - 1)
                stdev_latency = variance ** 0.5
        
        aggregated_results.append({
            "timestamp": now_ms(),
            "ps_per_site": ps_per_site,
            "mode": mode,
            "site": site,
            "avg_ms": round(avg_latency, 2),
            "stdev_ms": round(stdev_latency, 2),
            "count_2min": total_prestar_ok
        })
    
    # Write CSV
    typer.echo(f"Writing results to {out}...")
    
    # Check if file exists to determine if we need headers
    file_exists = out.exists()
    
    with open(out, 'a', newline='') as csvfile:
        fieldnames = ["timestamp", "ps_per_site", "mode", "site", "avg_ms", "stdev_ms", "count_2min"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header if file is new
        if not file_exists:
            writer.writeheader()
        
        # Write results
        for result in aggregated_results:
            writer.writerow(result)
    
    # Print summary
    typer.echo("\n" + "="*60)
    typer.echo("LOAD TEST SUMMARY")
    typer.echo("="*60)
    
    for result in aggregated_results:
        typer.echo(f"Site {result['site']}:")
        typer.echo(f"  Average latency: {result['avg_ms']:.2f}ms")
        typer.echo(f"  Std deviation: {result['stdev_ms']:.2f}ms")
        typer.echo(f"  PRESTAR OK count: {result['count_2min']}")
        typer.echo()
    
    typer.echo(f"Results written to: {out}")


if __name__ == "__main__":
    app()
