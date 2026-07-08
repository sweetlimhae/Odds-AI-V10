# Odds AI V10 Practical

## 핵심 변경
- Kelly 최대 10% 제한
- Sharp/Steam 낮은데 99% 강추천 뜨는 문제 보정
- 강추천 기준 강화: Sharp 80+, Steam 70+ 필요
- Consensus 빈 값 방지
- 안전형 / 평균형 / 도전형 3폴더만 추천
- 같은 경기 중복 제거
- 3폴더별 예상 적중률, 추천 금액, 메모 표시

## 데이터 소스
- 축구: Liveman
- 야구/농구/하키: 1순위 사이트 구조 유지

## Render
Build Command:
pip install -r requirements.txt

Start Command:
gunicorn app:app
