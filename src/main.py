import asyncio
import os
import shutil
import subprocess
import sys
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


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

    async with streamablehttp_client(hf_mcp_url, headers=headers) as (
            read_stream,
            write_stream,
            _,
    ):
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


async def fetch_apnews():
    """Fetches the AP News homepage and prints basic details."""
    print("\n--- 4. Fetching AP News Web Page ---")
    url = "https://apnews.com/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        print(f"Status Code: {response.status_code}")
        print(f"Fetched {len(response.text)} characters from {url}")
        print(f"Snippet:\n{response.text[:300].strip()}...")


async def main():
    try:
        update_and_run_node()
        await interact_with_hf_mcp()
        await fetch_apnews()
    except subprocess.CalledProcessError as e:
        print(f"Subprocess failed with exit code {e.returncode}", file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())