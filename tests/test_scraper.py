import pytest
from unittest.mock import MagicMock
import httpx
from intel_graph.nodes import scrape_domain

# ==========================================
# 1. TEST GRACEFUL FAILURE ROUTING
# ==========================================

def test_scrape_domain_invalid_url():
    """Ensure the utility catches broken or invalid domains gracefully without crashing the engine."""
    # Running a completely fake domain will trigger an httpx ConnectError
    result = scrape_domain("this-is-a-completely-fake-and-broken-domain-xyz.com")
    
    # Assert that it returns our custom error string instead of throwing an unhandled exception
    assert result.startswith("Error scraping target domain")
    assert "ConnectError" in result or "Name or service not known" in result

# ==========================================
# 2. TEST HTML BLOAT CLEANING (WITH MOCKING)
# ==========================================

def test_scraper_strips_html_bloat_successfully(mocker):
    """
    Ensures that the scraper correctly strips out scripts, styles, headers, 
    and footers, leaving only raw text content under the character limit.
    """
    # 1. Create a mock HTML string containing elements our scraper should delete
    mock_html = """
    <html>
        <head><title>Test B2B Company</title></head>
        <body>
            <header><a href="/">Home Link</a></header>
            <nav><ul><li>About</li></ul></nav>
            
            <main>
                <h1>We automate business workflows</h1>
                <p>Our platform helps scale modern revenue systems operations.</p>
            </main>
            
            <script type="text/javascript">console.log('Ignore this JavaScript code');</script>
            <style>body { background: blue; }</style>
            <footer>Copyright 2026 Legal Text Info</footer>
        </body>
    </html>
    """
    
    # 2. Mock the httpx Client request lifecycle context manager
    mock_response = MagicMock()
    mock_response.text = mock_html
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = mock_response
    
    # Intercept the httpx.Client call inside nodes.py and swap it with our mock
    mocker.patch("httpx.Client", return_value=mock_client)
    
    # 3. Execute the function against our controlled environment
    cleaned_result = scrape_domain("mocked-company.com")
    
    # 4. Run explicit structural assertions
    # The main text content must be retained
    assert "We automate business workflows" in cleaned_result
    assert "Our platform helps scale modern revenue systems operations." in cleaned_result
    
    # Code blocks, styling, navigation parameters, and legal footnotes must be aggressively stripped
    assert "console.log" not in cleaned_result
    assert "background: blue" not in cleaned_result
    assert "Home Link" not in cleaned_result
    assert "Copyright 2026 Legal Text Info" not in cleaned_result