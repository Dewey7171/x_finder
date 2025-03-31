import streamlit as st
import requests
import os
from PIL import Image
from io import BytesIO
import time

# 서버 URL을 환경 변수에서 가져오기
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
# SERVER_URL = st.secrets["SERVER_URL"]
st.title("The keywords that built your Web3 identity")

username = st.text_input("X Account")

# 리트라이 함수 정의
def retry_request(url, retries=5, delay=2):
    """주어진 URL에 대해 리트라이를 수행하는 함수"""
    for attempt in range(retries):
        response = requests.get(url)
        if response.status_code == 200:
            return response
        else:
            # 실패 시 대기 후 재시도
            time.sleep(delay)  # delay(초)만큼 기다리기
    return None  # 최대 리트라이 횟수를 초과한 경우

# 요청 처리 중인지 여부를 세션 상태로 추적
if 'is_processing' not in st.session_state:
    st.session_state['is_processing'] = False  # 요청이 처리 중인지 아닌지 추적

# 버튼 클릭 후 60초 동안 비활성화하는 로직
if 'last_click_time' not in st.session_state:
    st.session_state['last_click_time'] = 0  # 마지막 클릭 시간을 저장

# 현재 시간과 마지막 클릭 시간 비교
current_time = time.time()
button_disabled = (current_time - st.session_state['last_click_time']) < 60

# Start 버튼을 포함하는 폼
with st.form(key='start_form'):
    start_button = st.form_submit_button("Start", disabled=st.session_state['is_processing'] or button_disabled)

if start_button:
    if username:  # 사용자 아이디가 입력된 경우에만 실행
        # 버튼 클릭 시간을 저장
        st.session_state['last_click_time'] = current_time

        # 요청이 진행 중임을 표시
        st.session_state['is_processing'] = True

        # 트윗 크롤링 요청
        response = requests.post(f"{SERVER_URL}/scrape", json={"username": username})

        # 분석 완료 후 이미지 URL 요청
        if response.status_code == 200:
            st.success("Analysis complete")
            filename = response.json().get("file")
            image_name = filename.replace('.json', '.png')

            # 워드클라우드 이미지 경로 가져오기 (리트라이 적용)
            wordcloud_response = retry_request(f"{SERVER_URL}/wordcloud/{image_name}", retries=5)

            if wordcloud_response:
                image_file = wordcloud_response.json().get("image_path")
                if image_file:
                    # 이미지 파일을 서버의 'static' 폴더에서 로드
                    image_url = f"{SERVER_URL}/{image_file}"

                    # 이미지를 다운로드 (리트라이 적용)
                    image_response = retry_request(image_url, retries=5)

                    if image_response:
                        # 이미지 다운로드 및 표시
                        image = Image.open(BytesIO(image_response.content))
                        st.image(image, caption="Your voice, visualized", use_container_width=True)
                    else:
                        st.error("Image download failed after 5 attempts.")
                else:
                    st.error("No image file path available.")
            else:
                st.error("Failed to generate wordcloud image after 5 attempts.")

        # 작업이 끝나면 요청 처리 상태를 변경
        st.session_state['is_processing'] = False
    else:
        st.error("Please enter a username.")
