import csv
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = "http://127.0.0.1:8000/api/services"

REQUEST_TIMEOUT = 15

# Small delay between requests to avoid hitting government
# servers too aggressively.
DELAY_BETWEEN_REQUESTS = 0.15

OUTPUT_DIR = Path(__file__).resolve().parent / "link_test_results"

# Some government servers reject requests without a browser-like
# User-Agent.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
}


# ============================================================
# HELPERS
# ============================================================

def clean_url(url):
    """Clean and normalize a URL."""
    if not url:
        return ""

    url = str(url).strip()

    if not url:
        return ""

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url


def get_domain(url):
    """Return the domain from a URL."""
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def classify_status(status_code):
    """
    Classify HTTP response codes.

    Note:
    200-399 are considered reachable because many government
    portals redirect users before reaching the final page.
    """

    if 200 <= status_code < 300:
        return "PASS"

    if 300 <= status_code < 400:
        return "REDIRECT"

    if status_code in (401, 403):
        return "ACCESS_RESTRICTED"

    if status_code == 404:
        return "NOT_FOUND"

    if 400 <= status_code < 500:
        return "CLIENT_ERROR"

    if 500 <= status_code < 600:
        return "SERVER_ERROR"

    return "UNKNOWN"


def test_url(session, url):
    """
    Test a URL.

    First attempts HEAD.
    If HEAD is blocked/not supported, falls back to GET.
    """

    url = clean_url(url)

    if not url:
        return {
            "status": "NO_URL",
            "status_code": "",
            "final_url": "",
            "redirected": False,
            "response_time": "",
            "error": "URL is empty",
        }

    start_time = time.perf_counter()

    try:
        # ----------------------------------------------------
        # Try HEAD first
        # ----------------------------------------------------

        response = session.head(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        # Some websites don't properly support HEAD.
        # Fall back to GET for those.
        if response.status_code in (405, 501) or response.status_code >= 500:
            response = session.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                stream=True,
            )

        elapsed = round(time.perf_counter() - start_time, 3)

        final_url = response.url or url

        return {
            "status": classify_status(response.status_code),
            "status_code": response.status_code,
            "final_url": final_url,
            "redirected": final_url.rstrip("/") != url.rstrip("/"),
            "response_time": elapsed,
            "error": "",
        }

    except requests.exceptions.SSLError as error:
        elapsed = round(time.perf_counter() - start_time, 3)

        return {
            "status": "SSL_ERROR",
            "status_code": "",
            "final_url": "",
            "redirected": False,
            "response_time": elapsed,
            "error": str(error),
        }

    except requests.exceptions.Timeout as error:
        elapsed = round(time.perf_counter() - start_time, 3)

        return {
            "status": "TIMEOUT",
            "status_code": "",
            "final_url": "",
            "redirected": False,
            "response_time": elapsed,
            "error": str(error),
        }

    except requests.exceptions.ConnectionError as error:
        elapsed = round(time.perf_counter() - start_time, 3)

        return {
            "status": "CONNECTION_ERROR",
            "status_code": "",
            "final_url": "",
            "redirected": False,
            "response_time": elapsed,
            "error": str(error),
        }

    except requests.exceptions.RequestException as error:
        elapsed = round(time.perf_counter() - start_time, 3)

        return {
            "status": "REQUEST_ERROR",
            "status_code": "",
            "final_url": "",
            "redirected": False,
            "response_time": elapsed,
            "error": str(error),
        }

    except Exception as error:
        elapsed = round(time.perf_counter() - start_time, 3)

        return {
            "status": "ERROR",
            "status_code": "",
            "final_url": "",
            "redirected": False,
            "response_time": elapsed,
            "error": str(error),
        }


# ============================================================
# FETCH SERVICES FROM FASTAPI
# ============================================================

def fetch_services():
    print()
    print("=" * 70)
    print("Fetching services from GovNavigator API")
    print("=" * 70)
    print(f"API: {API_URL}")
    print()

    try:
        response = requests.get(
            API_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        # Support either:
        # [...]
        # or {"services": [...]}
        if isinstance(data, list):
            services = data
        elif isinstance(data, dict):
            services = data.get("services", [])

            if not services:
                # Try common alternate keys
                services = (
                    data.get("data")
                    or data.get("items")
                    or data.get("results")
                    or []
                )
        else:
            services = []

        if not isinstance(services, list):
            raise ValueError("Unexpected /api/services response format.")

        return services

    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to FastAPI.")
        print()
        print("Make sure your backend is running:")
        print()
        print("    uvicorn main:app --reload")
        print()
        raise SystemExit(1)

    except requests.exceptions.Timeout:
        print("ERROR: FastAPI request timed out.")
        raise SystemExit(1)

    except requests.exceptions.RequestException as error:
        print(f"ERROR: API request failed: {error}")
        raise SystemExit(1)

    except ValueError as error:
        print(f"ERROR: Could not read API response: {error}")
        raise SystemExit(1)


# ============================================================
# MAIN TEST
# ============================================================

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    services = fetch_services()

    total_services = len(services)

    print(f"Records returned by API: {total_services}")
    print()

    if total_services == 0:
        print("ERROR: No services were returned.")
        raise SystemExit(1)

    if total_services != 792:
        print(
            "WARNING: Expected 792 service/state records, "
            f"but API returned {total_services}."
        )
        print()
        print(
            "This usually means the 792-record seed has not "
            "been applied to the database yet."
        )
        print()

    print("=" * 70)
    print("STARTING LINK TEST")
    print("=" * 70)
    print()

    session = requests.Session()

    results = []

    counts = {}

    start_all = time.perf_counter()

    for index, service in enumerate(services, start=1):

        service_id = service.get("id", "")

        service_name = (
            service.get("name")
            or service.get("service_name")
            or ""
        )

        state_id = service.get("state_id", "")

        state_name = (
            service.get("state_name")
            or service.get("state")
            or ""
        )

        url = (
            service.get("official_portal_url")
            or service.get("officialPortalUrl")
            or service.get("url")
            or ""
        )

        url = clean_url(url)

        result = test_url(session, url)

        status = result["status"]

        counts[status] = counts.get(status, 0) + 1

        row = {
            "record_number": index,
            "service_id": service_id,
            "service_name": service_name,
            "state_id": state_id,
            "state_name": state_name,
            "url": url,
            "domain": get_domain(url),
            "status": status,
            "status_code": result["status_code"],
            "final_url": result["final_url"],
            "redirected": result["redirected"],
            "response_time_seconds": result["response_time"],
            "error": result["error"],
        }

        results.append(row)

        # ----------------------------------------------------
        # Console output
        # ----------------------------------------------------

        print(
            f"[{index:03d}/{total_services}] "
            f"{status:<20} "
            f"{service_name[:32]:<32} "
            f"{state_name[:22]}"
        )

        time.sleep(DELAY_BETWEEN_REQUESTS)

    total_time = round(time.perf_counter() - start_all, 2)

    # ========================================================
    # WRITE COMPLETE CSV
    # ========================================================

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    all_results_file = (
        OUTPUT_DIR / f"all_link_results_{timestamp}.csv"
    )

    fieldnames = [
        "record_number",
        "service_id",
        "service_name",
        "state_id",
        "state_name",
        "url",
        "domain",
        "status",
        "status_code",
        "final_url",
        "redirected",
        "response_time_seconds",
        "error",
    ]

    with open(
        all_results_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(results)

    # ========================================================
    # WRITE PROBLEM LINKS CSV
    # ========================================================

    problem_statuses = {
        "NO_URL",
        "NOT_FOUND",
        "CLIENT_ERROR",
        "SERVER_ERROR",
        "ACCESS_RESTRICTED",
        "SSL_ERROR",
        "TIMEOUT",
        "CONNECTION_ERROR",
        "REQUEST_ERROR",
        "ERROR",
        "UNKNOWN",
    }

    problems = [
        row
        for row in results
        if row["status"] in problem_statuses
    ]

    problem_file = (
        OUTPUT_DIR / f"problem_links_{timestamp}.csv"
    )

    with open(
        problem_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(problems)

    # ========================================================
    # WRITE REDIRECTS CSV
    # ========================================================

    redirects = [
        row
        for row in results
        if row["status"] == "REDIRECT"
        or row["redirected"]
    ]

    redirect_file = (
        OUTPUT_DIR / f"redirects_{timestamp}.csv"
    )

    with open(
        redirect_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(redirects)

    # ========================================================
    # SUMMARY
    # ========================================================

    passed = counts.get("PASS", 0)
    redirected = counts.get("REDIRECT", 0)
    restricted = counts.get("ACCESS_RESTRICTED", 0)

    failed = (
        total_services
        - passed
        - redirected
    )

    reachable = passed + redirected

    percentage = (
        (reachable / total_services) * 100
        if total_services
        else 0
    )

    summary_file = (
        OUTPUT_DIR / f"summary_{timestamp}.txt"
    )

    summary_lines = [
        "=" * 70,
        "GOVNAVIGATOR OFFICIAL LINK TEST REPORT",
        "=" * 70,
        "",
        f"Test time       : {datetime.now().isoformat()}",
        f"API             : {API_URL}",
        f"Records tested  : {total_services}",
        f"Expected        : 792",
        f"Test duration   : {total_time} seconds",
        "",
        "-" * 70,
        "RESULTS",
        "-" * 70,
        "",
        f"PASS            : {passed}",
        f"REDIRECT        : {redirected}",
        f"ACCESS_RESTRICTED: {restricted}",
        f"OTHER FAILURES  : {failed}",
        f"REACHABLE       : {reachable}",
        f"REACHABILITY %  : {percentage:.2f}%",
        "",
        "-" * 70,
        "STATUS BREAKDOWN",
        "-" * 70,
        "",
    ]

    for status, count in sorted(counts.items()):
        summary_lines.append(
            f"{status:<22}: {count}"
        )

    summary_lines.extend(
        [
            "",
            "-" * 70,
            "OUTPUT FILES",
            "-" * 70,
            "",
            f"All results : {all_results_file}",
            f"Problems    : {problem_file}",
            f"Redirects   : {redirect_file}",
            f"Summary     : {summary_file}",
            "",
        ]
    )

    summary_text = "\n".join(summary_lines)

    with open(
        summary_file,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(summary_text)

    # ========================================================
    # FINAL CONSOLE REPORT
    # ========================================================

    print()
    print()
    print("=" * 70)
    print("GOVNAVIGATOR LINK TEST COMPLETE")
    print("=" * 70)
    print()

    print(f"Records tested : {total_services}")
    print(f"Expected       : 792")
    print()
    print(f"PASS           : {passed}")
    print(f"REDIRECT       : {redirected}")
    print(f"Restricted     : {restricted}")
    print(f"Other failures : {failed}")
    print()
    print(f"Reachable      : {reachable}/{total_services}")
    print(f"Reachability   : {percentage:.2f}%")
    print()
    print(f"Duration       : {total_time} seconds")
    print()

    print("=" * 70)
    print("REPORT FILES")
    print("=" * 70)
    print()

    print(f"All results:")
    print(all_results_file)
    print()

    print(f"Problem links:")
    print(problem_file)
    print()

    print(f"Redirects:")
    print(redirect_file)
    print()

    print(f"Summary:")
    print(summary_file)
    print()

    if reachable == total_services:
        print("🎉 ALL 792 LINKS ARE REACHABLE!")
    elif reachable > 0:
        print(
            f"⚠️ {reachable} of {total_services} links are reachable."
        )
        print(
            "Check problem_links_*.csv for links requiring investigation."
        )
    else:
        print("❌ No links were reachable.")

    print()


if __name__ == "__main__":
    main()