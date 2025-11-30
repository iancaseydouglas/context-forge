import typer
import os
from pathlib import Path
from rich.console import Console
from toolz import pipe

from context_forge.core.state import ForgeState, RepoConfig
from context_forge.ops.compression import generate_vbt_stubs, pack_repositories
from context_forge.ops.gateway import upload_to_gemini

app = typer.Typer()
console = Console()

@app.command()
def hydrate(
    active: Path = typer.Option(..., help="Path to Active Repo (Read/Write)"),
    vbt: Path = typer.Option(..., help="Path to VectorBT Pro (Read-Only)"),
    charts: Path = typer.Option(..., help="Path to Lightweight Charts (Read-Only)"),
):
    """
    Hydrate the Quant Development Context.
    
    1. Stubs VectorBT Pro (Numba/Python).
    2. Compresses Lightweight Charts (TypeScript).
    3. Caches Libraries in Gemini 3.
    4. Generates IDE Configs.
    """
    console.print("[bold blue]🚀 Context Forge: Initializing...[/bold blue]")

    # 1. Initialize Immutable State
    initial_state = ForgeState(
        active_repo=RepoConfig(path=active.resolve(), role="active", strategy="full", language="python"),
        vbt_repo=RepoConfig(path=vbt.resolve(), role="reference", strategy="stub", language="python"),
        charts_repo=RepoConfig(path=charts.resolve(), role="reference", strategy="compress", language="typescript"),
    )

    # 2. Execute Functional Pipeline
    # The state flows through each function, returning a new state each time.
    final_state = pipe(
        initial_state,
        generate_vbt_stubs,
        pack_repositories,
        upload_to_gemini
    )

    # 3. Output Handling
    if final_state.error:
        console.print(f"[bold red]❌ Failure:[/bold red] {final_state.error}")
        for log in final_state.logs:
            console.print(f"  {log}")
        raise typer.Exit(code=1)

    # 4. Success & IDE Injection
    console.print(f"[bold green]✅ Context Cached Successfully![/bold green]")
    for log in final_state.logs:
        console.print(f"  [dim]{log}[/dim]")
        
    console.print(f"\nCache Name: [bold cyan]{final_state.cache_name}[/bold cyan]")
    console.print(f"Expires:    {final_state.cache_expire_time}")
    
    # 5. Inject into Google Antigravity / Cursor rules
    rule_path = active / ".antigravity/rules.md"
    
    try:
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        
        # We append/overwrite the context rules
        with open(rule_path, "w") as f:
            f.write("# Context Forge Configuration\n\n")
            f.write(f"**Gemini Cache ID:** `{final_state.cache_name}`\n")
            f.write(f"**Generated:** {os.popen('date').read().strip()}\n\n")
            f.write("## Context Contents\n")
            f.write("- **VectorBT Pro:** Python Stubs (.pyi)\n")
            f.write("- **Lightweight Charts:** Compressed TypeScript\n")
            f.write("- **Active Repo:** Full Source\n")
        
        console.print(f"📝 Injected Cache ID into: [underline]{rule_path}[/underline]")
        
    except Exception as e:
        console.print(f"[yellow]⚠️ Could not write IDE config: {e}[/yellow]")

if __name__ == "__main__":
    app()