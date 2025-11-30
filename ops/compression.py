import subprocess
import shutil
from pathlib import Path
from context_forge.core.state import ForgeState

def generate_vbt_stubs(state: ForgeState) -> ForgeState:
    """
    Step 1: Run 'stubgen' on VectorBT Pro.
    
    Why: VBT Pro is huge and relies on Numba compilation. The raw source code is 
    too token-heavy and often confusing to LLMs due to dynamic dispatch. 
    Stubs (.pyi) provide the exact type signatures needed for the LLM to write 
    correct code, at ~5% of the token cost.
    """
    if not state.is_valid: return state

    target_dir = Path("/tmp/forge/vbt_stubs")
    
    # Clean up previous run
    if target_dir.exists(): 
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    state = state.add_log(f"⚡ Generating Stubs for VectorBT Pro at {state.vbt_repo.path}...")

    try:
        # stubgen is installed via 'mypy' dependency
        cmd =
        
        # We capture output to avoid polluting the terminal
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Success: Update state with location of the generated stubs
        return state.model_copy(update={"vbt_stub_path": target_dir})
        
    except subprocess.CalledProcessError as e:
        return state.fail(f"Stubgen failed (exit {e.returncode}): {e.stderr.decode()}")
    except Exception as e:
        return state.fail(f"VBT Processing error: {str(e)}")

def pack_repositories(state: ForgeState) -> ForgeState:
    """
    Step 2: Serialize all code into XML format using Repomix.
    
    This function handles three distinct packing strategies:
    1. VBT: Packs the *stubs* we just generated.
    2. Charts: Packs the *source* but uses Tree-sitter compression.
    3. Active: Packs the *source* with full fidelity (comments included).
    """
    if not state.is_valid: return state

    # Helper inner function for side-effects (subprocess execution)
    def run_repomix(cwd: Path, output_filename: str, compress: bool, remove_comments: bool) -> Path:
        cmd = ["npx", "repomix", "--style", "xml", "--output", output_filename]
        
        # Feature flags
        if compress: 
            cmd.append("--compress")
        if remove_comments: 
            cmd.append("--remove-comments")
            
        # Repomix config overrides for strict ignore patterns
        # We ignore tests and lockfiles to save tokens
        cmd.extend(["--ignore", "**/*.test.ts,**/*.spec.py,**/tests/**,**/*.lock"])

        subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)
        return cwd / output_filename

    try:
        # A. Pack VBT Stubs (Reference)
        state = state.add_log("📦 Packing VBT Pro Stubs (XML)...")
        vbt_xml_path = run_repomix(
            cwd=state.vbt_stub_path, # type: ignore (checked by is_valid logic roughly, but safe here)
            output_filename="vbt_context.xml", 
            compress=False,          # Stubs are already minimal
            remove_comments=True
        )

        # B. Pack Lightweight Charts (Reference)
        state = state.add_log("📦 Packing Lightweight Charts (Compressed XML)...")
        charts_xml_path = run_repomix(
            cwd=state.charts_repo.path,
            output_filename="charts_context.xml",
            compress=True,           # Use Tree-sitter to strip implementation
            remove_comments=False    # Keep JSDoc comments for API hints
        )

        # C. Pack Active Repo (Active)
        state = state.add_log("📦 Packing Active Repository (Full Fidelity)...")
        active_xml_path = run_repomix(
            cwd=state.active_repo.path,
            output_filename="active_context.xml",
            compress=False,
            remove_comments=False
        )

        # D. Merge Logic
        # We concatenate the XML files into a single master context stream
        master_path = Path("/tmp/forge/master_context.xml")
        
        state = state.add_log(f"🔗 Merging context nodes into {master_path}...")
        
        with open(master_path, 'w') as master:
            master.write('<context_root>\n')
            
            # 1. Dependency: VBT
            master.write(f'  <library name="vectorbtpro" type="stubbed_reference">\n')
            with open(vbt_xml_path, 'r') as f: master.write(f.read())
            master.write('  </library>\n')

            # 2. Dependency: Charts
            master.write(f'  <library name="lightweight-charts" type="compressed_reference">\n')
            with open(charts_xml_path, 'r') as f: master.write(f.read())
            master.write('  </library>\n')
            
            # 3. Active Work
            master.write(f'  <workspace name="active_repository" type="full_fidelity">\n')
            with open(active_xml_path, 'r') as f: master.write(f.read())
            master.write('  </workspace>\n')
            
            master.write('</context_root>\n')

        return state.model_copy(update={"merged_context_path": master_path})

    except Exception as e:
        return state.fail(f"Repomix Packing failed: {str(e)}")