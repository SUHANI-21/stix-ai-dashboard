import subprocess


def call_ollama(prompt, model="mistral"):
    """Call Ollama LLM with a prompt."""
    try:
        cmd = ["ollama", "run", model]

        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        out, err = p.communicate(prompt, timeout=30)

        if err:
            print(f"LLM Error: {err}", flush=True)
        
        if out and out.strip():
            return out.strip()
        
        return None

    except subprocess.TimeoutExpired:
        print("LLM call timed out", flush=True)
        return None
    except FileNotFoundError:
        print("Ollama not found in PATH", flush=True)
        return None
    except Exception as e:
        print(f"LLM exception: {e}", flush=True)
        return None
