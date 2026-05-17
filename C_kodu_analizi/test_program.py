from analyzer import kodu_tara, fonksiyon_durumlarini_hesapla
from app import app


def run_analyzer_tests():
    print("=== Analyzer Tests ===")
    cases = [
        {
            "name": "unsafe_gets_detected",
            "code": "int main(){ char buf[16]; gets(buf); return 0; }",
            "expected_functions": {"gets"},
        },
        {
            "name": "unsafe_scanf_percent_s_detected",
            "code": 'int main(){ char name[10]; scanf("%s", name); return 0; }',
            "expected_functions": {"scanf"},
        },
        {
            "name": "safe_copy_not_reported",
            "code": "int main(){ char a[10]; char b[10]; memcpy(a, b, sizeof(a)); return 0; }",
            "expected_functions": set(),
        },
        {
            "name": "format_string_vulnerability_detected",
            "code": "int main(){ char *user_input; printf(user_input); return 0; }",
            "expected_functions": {"printf"},
        },
        {
            "name": "mixed_multiple_vulnerabilities",
            "code": "int main(){ char b[8]; gets(b); sprintf(b, \"%s\", \"x\"); return 0; }",
            "expected_functions": {"gets", "sprintf"},
        },
        {
            "name": "safe_strncat_remaining_space_not_reported",
            "code": "int main(){ char dest[32] = \"A\"; char src[8] = \"B\"; strncat(dest, src, sizeof(dest) - strlen(dest) - 1); return 0; }",
            "expected_functions": set(),
        },
        {
            "name": "line_comment_ignored",
            "code": "int main(){ // gets(buf);\n return 0; }",
            "expected_functions": set(),
        },
        {
            "name": "block_comment_ignored",
            "code": "int main(){ /* strcpy(dst, src); */ return 0; }",
            "expected_functions": set(),
        },
        {
            "name": "comment_null_does_not_hide_free_issue",
            "code": "int main(){ free(ptr); // NULL yazildi ama yorum\n return 0; }",
            "expected_functions": {"free"},
        },
    ]

    passed = 0
    failed = 0

    for case in cases:
        results = kodu_tara(case["code"])
        found_functions = {item["fonksiyon"] for item in results}
        expected = case["expected_functions"]
        ok = found_functions == expected

        if ok:
            passed += 1
            print(f"[PASS] {case['name']} -> found: {sorted(found_functions)}")
        else:
            failed += 1
            print(
                f"[FAIL] {case['name']} -> expected: {sorted(expected)}, found: {sorted(found_functions)}"
            )

    print(f"Analyzer summary: {passed} passed, {failed} failed\n")
    return passed, failed


def run_function_status_tests():
    print("=== Function Status Tests ===")
    cases = [
        {
            "name": "gets_marked_vulnerable",
            "code": "int main(){ char b[8]; gets(b); return 0; }",
            "expected": {"gets": {"durum": "zafiyetli", "kullanim_sayisi": 1, "bulgu_sayisi": 1}},
        },
        {
            "name": "safe_scanf_marked_safe",
            "code": 'int main(){ char b[8]; scanf("%7s", b); return 0; }',
            "expected": {"scanf": {"durum": "guvenli", "kullanim_sayisi": 1, "bulgu_sayisi": 0}},
        },
        {
            "name": "unused_function_marked_unused",
            "code": 'int main(){ printf("%s", "ok"); return 0; }',
            "expected": {"system": {"durum": "kullanilmadi", "kullanim_sayisi": 0, "bulgu_sayisi": 0}},
        },
        {
            "name": "variant_normalized_for_usage_and_findings",
            "code": "int main(){ strncat(dst, src, strlen(src)); return 0; }",
            "expected": {"strcat": {"durum": "zafiyetli", "kullanim_sayisi": 1, "bulgu_sayisi": 1}},
        },
        {
            "name": "safe_strncat_marked_safe",
            "code": "int main(){ strncat(dest, src, sizeof(dest) - strlen(dest) - 1); return 0; }",
            "expected": {"strcat": {"durum": "guvenli", "kullanim_sayisi": 1, "bulgu_sayisi": 0}},
        },
        {
            "name": "commented_usage_is_not_counted",
            "code": "int main(){ // gets(buf);\n return 0; }",
            "expected": {"gets": {"durum": "kullanilmadi", "kullanim_sayisi": 0, "bulgu_sayisi": 0}},
        },
    ]

    passed = 0
    failed = 0

    for case in cases:
        status_map = fonksiyon_durumlarini_hesapla(case["code"])
        ok = True
        for func_name, expected_data in case["expected"].items():
            for key, expected_value in expected_data.items():
                if status_map[func_name][key] != expected_value:
                    ok = False
                    break
            if not ok:
                break

        if ok:
            passed += 1
            print(f"[PASS] {case['name']}")
        else:
            failed += 1
            print(f"[FAIL] {case['name']} -> got: {status_map}")

    print(f"Function status summary: {passed} passed, {failed} failed\n")
    return passed, failed


def run_api_tests():
    print("=== API Tests ===")
    client = app.test_client()
    passed = 0
    failed = 0

    checks = []

    r1 = client.get("/")
    checks.append(("GET / returns 200", r1.status_code == 200))

    r2 = client.get("/api/scan")
    checks.append(("GET /api/scan returns 200", r2.status_code == 200))
    checks.append(("GET /api/scan status is ready", r2.get_json().get("status") == "ready"))

    r3 = client.post("/api/scan", json={})
    checks.append(("POST /api/scan without code returns 400", r3.status_code == 400))

    r4 = client.post("/api/scan", json={"code": "gets(buf);"})
    body4 = r4.get_json()
    checks.append(("POST /api/scan with code returns 200", r4.status_code == 200))
    checks.append(("POST /api/scan status is success", body4.get("status") == "success"))
    checks.append(("POST /api/scan reports one vulnerability", body4.get("toplam_zafiyet") == 1))
    checks.append(
        (
            "POST /api/scan identifies gets",
            body4.get("zafiyetler", [{}])[0].get("fonksiyon") == "gets",
        )
    )
    checks.append(
        (
            "POST /api/scan returns function status details",
            body4.get("fonksiyon_durumlari", {}).get("gets", {}).get("durum") == "zafiyetli",
        )
    )

    for label, ok in checks:
        if ok:
            passed += 1
            print(f"[PASS] {label}")
        else:
            failed += 1
            print(f"[FAIL] {label}")

    print(f"API summary: {passed} passed, {failed} failed\n")
    return passed, failed


if __name__ == "__main__":
    analyzer_passed, analyzer_failed = run_analyzer_tests()
    status_passed, status_failed = run_function_status_tests()
    api_passed, api_failed = run_api_tests()

    total_passed = analyzer_passed + status_passed + api_passed
    total_failed = analyzer_failed + status_failed + api_failed

    print("=== Final Summary ===")
    print(f"Total: {total_passed} passed, {total_failed} failed")

    if total_failed > 0:
        raise SystemExit(1)
