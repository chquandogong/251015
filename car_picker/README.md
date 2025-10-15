# Car Picker Quiz

이 디렉터리는 자동차 이미지를 활용한 스트림릿 기반 퀴즈 앱입니다.

## 구성

- `app/`: Streamlit 앱 소스 코드
- `data/`: 메타데이터 생성 스크립트와 `car_labels.csv`(헤더만 포함)
- `dataset/`: 원본 자동차 이미지(깃에 커밋하지 말 것)
- `results/`: 퀴즈 결과 로그가 저장되는 위치(기본적으로 `.gitignore` 처리)

## 사용 방법

1. **데이터 준비**  
   `dataset/` 아래에 이미지가 위치해 있어야 합니다. 원본은  
   <https://github.com/nicolas-gervais/predicting-car-price-from-scraped-data/tree/master/picture-scraper>
   를 참고하세요.

2. **메타데이터 생성**  
   ```bash
   python car_picker/data/build_metadata.py
   ```
   실행하면 `car_picker/data/car_labels.csv`가 채워집니다.

3. **앱 실행**  
   ```bash
   streamlit run car_picker/app/streamlit_app.py
   ```
   난이도(상/중/하)를 선택하고 10문제 퀴즈를 진행할 수 있습니다.

> `car_picker/dataset/`과 `car_picker/results/`는 저장소에 포함되지 않도록 `.gitignore`에 설정돼 있습니다.
