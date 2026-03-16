"""
HTML → PDF conversion using Playwright (Chromium).

Install once on the server:
    pip install playwright
    playwright install chromium --with-deps

For Cloud Run, add to Dockerfile:
    RUN pip install playwright && playwright install chromium --with-deps
"""

import asyncio


async def html_to_pdf(html_content: str) -> bytes:
    """Render an HTML string to PDF bytes using Playwright Chromium.
    Waits for network (Google Fonts) to load before capturing."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        try:
            page = await browser.new_page()
            await page.set_content(html_content, wait_until="networkidle")
            pdf_bytes = await page.pdf(
                format="Letter",
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                print_background=True,
            )
            return pdf_bytes
        finally:
            await browser.close()
