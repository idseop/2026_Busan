"""Exercise the delivered website against independently stored analysis counts."""
from collections import defaultdict
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import csv
import hashlib
import json
import re
import threading

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "web/final"
OUT = ROOT / "data/processed/최종결과-20260915/browser_verification"
COUNTS = ROOT / "data/processed/동대응-전체결측제외-20260915/analysis/annual_type.csv"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    expected = defaultdict(int)
    with COUNTS.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            year, scope, kind = row["year"], row["scope"], row["EMRG_RSCU_ASSRT_NM"]
            count = int(row["receipt_count"])
            for yy in [year, "all"]:
                expected[(yy, scope, kind)] += count
                expected[(yy, scope, "all")] += count

    data = json.loads((SITE / "data/dashboard.json").read_text(encoding="utf-8"))
    errors, failed_requests, checks, time_checks = [], [], [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe",
            headless=True,
        )
        page = browser.new_page(viewport={"width": 1600, "height": 1100}, device_scale_factor=1)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("requestfailed", lambda request: failed_requests.append(request.url))
        page.goto((SITE / "index.html").as_uri(), wait_until="load")
        page.locator("#dashboard").wait_for(state="visible", timeout=30000)
        assert page.locator("#load-error").is_hidden()
        years = page.locator("#year option").evaluate_all("els => els.map(e => e.value)")
        assert set(map(str, range(2020, 2025))).issubset(years)
        assert set(years).issubset({"all", *map(str, range(2020, 2025))})
        kinds = ["all", "구급", "구조", "기타", "화재"]
        for year in years:
            page.select_option("#year", year)
            for scope in ["A", "B", "C"]:
                page.select_option("#scope", scope)
                for kind in kinds:
                    page.select_option("#type", kind)
                    want = expected[(year, scope, kind)]
                    page.wait_for_function(
                        "n => Number(document.querySelector('#metric-total').textContent.replace(/[^0-9]/g,'')) === n",
                        arg=want,
                    )
                    five = int(page.locator("#metric-five").inner_text().replace(",", ""))
                    assert five == expected[("all", scope, kind)]
                    assert page.locator("#trend-chart svg").count() == 1
                    assert "NaN" not in page.locator("#time-chart").inner_text()
                    checks.append({"year": year, "scope": scope, "type": kind, "count": want})
                    for dimension in ["month", "season", "weekday", "hourBand"]:
                        grouped = {}
                        for row in data["time"]:
                            if row["scope"] != scope or row["dimension"] != dimension:
                                continue
                            if year != "all" and str(row["year"]) != year:
                                continue
                            if kind != "all" and row["type"] != kind:
                                continue
                            entry = grouped.setdefault(str(row["value"]), {"count": 0, "days": {}})
                            entry["count"] += row["count"]
                            entry["days"][row["year"]] = row["calendarDays"]
                        wanted = sorted(x["count"] for x in grouped.values())
                        page.locator(f'[data-dimension="{dimension}"]').click()
                        titles = page.locator("#time-chart svg rect title").all_text_contents()
                        observed = sorted(float(re.search(r":\s*([\d,.]+)", t).group(1).replace(",", "")) for t in titles)
                        assert observed == wanted, (year, scope, kind, dimension, observed, wanted)
                        page.locator("#daily-rate").check()
                        titles = page.locator("#time-chart svg rect title").all_text_contents()
                        observed = sorted(float(re.search(r":\s*([\d,.]+)", t).group(1).replace(",", "")) for t in titles)
                        wanted_daily = sorted(x["count"] / sum(x["days"].values()) for x in grouped.values())
                        assert len(observed) == len(wanted_daily)
                        assert all(abs(a-b) <= 0.051 for a,b in zip(observed, wanted_daily))
                        page.locator("#daily-rate").uncheck()
                        assert page.locator('[data-dimension].selected').count() == 1
                        time_checks.append([year, scope, kind, dimension])
        page.select_option("#year", "2024")
        page.select_option("#scope", "A")
        page.select_option("#type", "all")
        for dimension in ["month", "season", "weekday", "hourBand"]:
            page.locator(f'[data-dimension="{dimension}"]').click()
            assert page.locator(f'[data-dimension="{dimension}"]').get_attribute("aria-pressed") == "true"
            assert page.locator("#time-chart svg").count() == 1
            page.locator("#daily-rate").check()
            assert "NaN" not in page.locator("#time-chart").inner_text()
            page.locator("#daily-rate").uncheck()
        page.locator('[data-dimension="month"]').click()

        assert page.locator("#district option").count() == 17
        assert page.locator("#district-map svg").count() == 1
        assert "2025-06-30" in page.locator("#map-source").inner_text()
        map_path = page.locator('#district-map path[data-district]').first
        map_name = map_path.get_attribute("data-district")
        map_path.focus()
        page.keyboard.press("Enter")
        assert page.locator("#district").input_value() == map_name
        page.select_option("#district", label="기장군")
        assert page.locator("#raw-dong option").count() > 0
        original_global_count = page.locator("#metric-total").inner_text()
        page.locator("#region-search").fill("존재하지않는동_qa")
        assert page.locator("#metric-total").inner_text() == original_global_count
        assert page.locator("#raw-dong").is_disabled() or page.locator("#raw-dong option").count() <= 1
        page.locator("#region-search").fill("")
        page.locator("#clear-district").click()

        for year in map(str, range(2020, 2025)):
            page.select_option("#year", year)
            page.locator("#population-search").fill("")
            assert page.locator("#population-dong option").count() == 205
            assert year in page.locator("#population-context").inner_text()
        page.select_option("#year", "2024")
        page.locator("#population-search").fill("존재하지않는행정동_qa")
        assert page.locator("#population-dong").is_disabled() or page.locator("#population-dong option").count() <= 1
        assert page.locator("#age-detail").is_hidden() or page.locator("#age-detail tbody tr").count() == 0
        page.locator("#population-search").fill("")
        page.locator('[data-age-mode="count"]').click()
        page.locator('[data-age-mode="share"]').click()
        assert page.locator('[data-age-mode].selected').count() == 1
        page.locator("#age-detail").evaluate("el => el.open = true")
        assert page.locator("#age-detail tbody tr").count() == 101
        observed_population = sum(int(re.sub(r"\D", "", x)) for x in page.locator("#age-detail tbody tr td:nth-child(2)").all_text_contents())
        pop_code = page.locator("#population-dong").input_value()
        pop_row = next(x for x in data["population"] if x["year"] == 2024 and str(x["code"]) == pop_code)
        assert observed_population == pop_row["total"]
        page.locator("#age-detail").evaluate("el => el.open = false")

        page.select_option("#type", "all")
        page.locator("#clear-district").click()
        for minimum, expected_count in [(1, 2325), (5, 1180), (10, 838), (20, 526)]:
            page.select_option("#candidate-min", str(minimum))
            assert f"{expected_count:,}개" in page.locator("#candidate-count").inner_text()
            assert page.locator("#candidate-cards .candidate").count() == 20
        page.locator("#candidate-more").click()
        assert page.locator("#candidate-cards .candidate").count() == 40
        page.select_option("#candidate-min", "1")
        assert "벌집" not in page.locator("#candidate-cards").inner_text()
        assert page.locator("#metric-retention").inner_text().count("%") <= 1
        assert len(page.locator("#type-chart .type-track i").evaluate_all("els => els.filter(e => e.getBoundingClientRect().height > 0 && e.getBoundingClientRect().width > 0)")) == 4
        assert page.locator("#retention-chart svg rect title").count() == 10

        page.evaluate("window.scrollTo(0,0)")
        page.screenshot(path=str(OUT / "desktop-overview.png"))
        page.screenshot(path=str(OUT / "desktop-full.png"), full_page=True)
        page.locator("#regions").scroll_into_view_if_needed()
        page.screenshot(path=str(OUT / "desktop-regions.png"))
        page.set_viewport_size({"width": 390, "height": 844})
        page.evaluate("window.scrollTo(0,0)")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        page.screenshot(path=str(OUT / "mobile-overview.png"))
        page.screenshot(path=str(OUT / "mobile-full.png"), full_page=True)
        assert not errors, errors
        assert not failed_requests, failed_requests

        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, *_):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(SITE)))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            page.goto(f"http://127.0.0.1:{server.server_port}/", wait_until="load")
            page.locator("#dashboard").wait_for(state="visible")
            assert page.locator("#metric-total").inner_text().replace(",", "").isdigit()
            assert not errors, errors
        finally:
            server.shutdown()
            server.server_close()
        browser.close()

    files = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in SITE.rglob("*") if p.is_file()}
    evidence = {
        "status": "passed",
        "count_source": str(COUNTS.relative_to(ROOT)),
        "count_source_sha256": hashlib.sha256(COUNTS.read_bytes()).hexdigest(),
        "filter_combinations": checks,
        "rendered_time_combinations_counts_and_daily_rates": time_checks,
        "file_and_http_entry_points": True,
        "population_all_five_years_205_options": True,
        "time_dimensions_and_daily_toggle": True,
        "empty_search_states": True,
        "single_age_101_rows_and_sum": True,
        "candidate_thresholds_and_pagination": True,
        "map_keyboard_and_reference_date": True,
        "mobile_no_horizontal_overflow": True,
        "page_errors": errors,
        "failed_requests": failed_requests,
        "site_sha256": files,
    }
    (OUT / "result.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PASS: {len(checks)} filter combinations, file/HTTP, population and mobile checks")


if __name__ == "__main__":
    main()
