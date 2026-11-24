import asyncio
import os
import shutil
import subprocess
import sys
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def update_and_run_node():
    """Updates npm packages and runs the JavaScript Hello World script."""
    npm_cmd = shutil.which("npm")
    node_cmd = shutil.which("node")

    if not npm_cmd or not node_cmd:
        raise RuntimeError(
            "Node.js (node/npm) is not installed or not in your system PATH."
        )

    print("--- 1. Updating Node dependencies ---")
    subprocess.run([npm_cmd, "update"], check=True)

    print("\n--- 2. Running JavaScript Hello World via Node ---")
    subprocess.run([node_cmd, "hello.js"], check=True)


async def interact_with_hf_mcp():
    """Connects to Hugging Face MCP server, lists tools, and calls hf_whoami."""
    print("\n--- 3. Connecting to Hugging Face MCP Server ---")
    hf_mcp_url = "https://huggingface.co/mcp"
    hf_token = os.environ.get("HF_TOKEN")

    headers = {}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
    else:
        print(
            "Warning: HF_TOKEN environment variable not set. "
            "hf_whoami may report unauthenticated/anonymous status."
        )

    # Newer MCP SDK versions no longer accept `headers`; custom headers are
    # supplied through a pre-configured httpx.AsyncClient instead.
    async with httpx.AsyncClient(
            headers=headers, follow_redirects=True, timeout=httpx.Timeout(30.0, read=300.0)
    ) as http_client:
        async with streamable_http_client(hf_mcp_url, http_client=http_client) as streams:
            # Newer SDKs yield (read, write); older ones yield (read, write, get_session_id).
            read_stream, write_stream = streams[0], streams[1]
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                tools_response = await session.list_tools()
                print("Available Hugging Face MCP Tools:")
                for tool in tools_response.tools:
                    print(f" - {tool.name}: {tool.description}")

                print("\nInvoking 'hf_whoami' tool...")
                whoami_result = await session.call_tool("hf_whoami", arguments={})
                for content in whoami_result.content:
                    if hasattr(content, "text"):
                        print(f"Result: {content.text}")
                    else:
                        print(f"Result: {content}")


async def fetch_modelop():
    """Fetches the ModelOp homepage and prints basic details."""
    print("--- 0. Fetching ModelOp Web Page ---")
    url = "https://www.modelop.com/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        print(f"Status Code: {response.status_code}")
        print(f"Fetched {len(response.text)} characters from {url}")
        print(f"Snippet:\n{response.text[:300].strip()}...")


async def fetch_apnews():
    """Fetches the AP News homepage and prints basic details."""
    print("\n--- 4. Fetching AP News Web Page ---")
    url = "https://apnews.com/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 403:
            print(
                "AP News blocked the request (HTTP 403, likely bot protection). "
                "Skipping this step."
            )
            return
        response.raise_for_status()
        print(f"Status Code: {response.status_code}")
        print(f"Fetched {len(response.text)} characters from {url}")
        print(f"Snippet:\n{response.text[:300].strip()}...")


def _flatten_exceptions(exc):
    """Recursively unwraps exception groups (e.g. from anyio TaskGroups)."""
    subs = getattr(exc, "exceptions", None)
    if subs:
        for sub in subs:
            yield from _flatten_exceptions(sub)
    else:
        yield exc


def _report_error(step_name, e):
    """Prints an error for a failed step without stopping the program."""
    if isinstance(e, subprocess.CalledProcessError):
        print(
            f"Error in {step_name}: subprocess failed with exit code {e.returncode}",
            file=sys.stderr,
        )
        return
    for inner in _flatten_exceptions(e):
        if isinstance(inner, httpx.HTTPStatusError):
            print(
                f"Error in {step_name}: HTTP {inner.response.status_code} "
                f"from {inner.request.url}",
                file=sys.stderr,
            )
        else:
            print(
                f"Error in {step_name}: {type(inner).__name__}: {inner}",
                file=sys.stderr,
            )


async def main():
    try:
        await fetch_modelop()
    except Exception as e:
        _report_error("fetch_modelop", e)

    print()
    try:
        update_and_run_node()
    except Exception as e:
        _report_error("update_and_run_node", e)

    try:
        await interact_with_hf_mcp()
    except Exception as e:
        _report_error("interact_with_hf_mcp", e)

    try:
        await fetch_apnews()
    except Exception as e:
        _report_error("fetch_apnews", e)


if __name__ == "__main__":
    asyncio.run(main())