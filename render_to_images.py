import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Windows UTF-8 설정
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES2_DIR = os.path.join(CURRENT_DIR, "images2")
HTML_FILE = os.path.join(IMAGES2_DIR, "render_diagrams.html")

os.makedirs(IMAGES2_DIR, exist_ok=True)

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1400,2000")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

print("🚀 Chrome 브라우저 시작 중...")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    file_url = "file:///" + HTML_FILE.replace("\\", "/")
    print(f"📄 HTML 파일 로딩: {file_url}")
    driver.get(file_url)

    # 렌더링 완료 대기
    time.sleep(3)

    diagram_cards = [
        ("01_system_architecture", "card-01", "diagram_01"),
        ("02_execution_flowchart", "card-02", "diagram_02"),
        ("03_class_diagram", "card-03", "diagram_03"),
    ]

    for name, card_id, diagram_id in diagram_cards:
        # 1. 카드 엘리먼트 PNG 스크린샷 저장
        card_el = driver.find_element(By.ID, card_id)
        png_path = os.path.join(IMAGES2_DIR, f"{name}.png")
        card_el.screenshot(png_path)
        print(f"✅ PNG 저장 완료: {png_path} ({os.path.getsize(png_path):,} bytes)")

        # 2. SVG 코드 추출 및 .svg 파일 저장
        diagram_el = driver.find_element(By.ID, diagram_id)
        svg_el = diagram_el.find_element(By.TAG_NAME, "svg")
        svg_code = svg_el.get_attribute("outerHTML")
        svg_path = os.path.join(IMAGES2_DIR, f"{name}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_code)
        print(f"✅ SVG 저장 완료: {svg_path} ({os.path.getsize(svg_path):,} bytes)")

    # 전체 페이지 스크린샷도 저장
    full_path = os.path.join(IMAGES2_DIR, "00_all_diagrams.png")
    driver.save_screenshot(full_path)
    print(f"✅ 전체 다이어그램 캡처 완료: {full_path} ({os.path.getsize(full_path):,} bytes)")

    print("\n🎉 모든 Mermaid 도식 도표가 images2 폴더에 성공적으로 저장되었습니다!")

finally:
    driver.quit()
