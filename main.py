# main.py
# ------------------------------------------------------------
# Solar API(solar-open2)를 사용하는 스트림릿 AI 채팅 앱
# 초보자도 이해할 수 있도록 한 줄 한 줄 한국어 주석을 달았습니다.
# ------------------------------------------------------------

import streamlit as st
from openai import OpenAI

# ------------------------------------------------------------
# 1) 페이지 기본 설정
# ------------------------------------------------------------
st.set_page_config(page_title="Solar AI 채팅", page_icon="💬")
st.title("💬 Solar AI 채팅 (solar-open2)")

# ------------------------------------------------------------
# 2) API 키 불러오기
#    - 코드에 직접 키를 쓰지 않고, 스트림릿의 "비밀 금고(secrets)"에서 불러옵니다.
#    - 스트림릿 클라우드에서는 앱 설정 > Secrets 메뉴에 아래처럼 적어두면 됩니다.
#      SOLAR_API_KEY = "여기에_실제_키_입력"
# ------------------------------------------------------------
try:
    SOLAR_API_KEY = st.secrets["SOLAR_API_KEY"]
except Exception:
    # secrets에 키가 없을 때, 에러 화면 대신 친절한 안내를 보여줍니다.
    st.error(
        "⚠️ API 키를 찾을 수 없어요.\n\n"
        "스트림릿 클라우드의 '앱 설정 > Secrets' 메뉴에 아래와 같이 등록해 주세요.\n\n"
        "SOLAR_API_KEY = \"여기에_실제_키_입력\""
    )
    st.stop()  # 키가 없으면 앱 실행을 여기서 멈춥니다.

# ------------------------------------------------------------
# 3) OpenAI 라이브러리를 이용해 Solar API에 접속할 클라이언트 만들기
#    - base_url을 Solar API 주소로 바꿔주면, openai 라이브러리 문법 그대로 사용할 수 있습니다.
# ------------------------------------------------------------
client = OpenAI(
    api_key=SOLAR_API_KEY,
    base_url="https://api.upstage.ai/v1",
)

# ------------------------------------------------------------
# 4) 시스템 프롬프트(AI의 성격/역할 지정)
#    - 대화 맨 앞에 항상 들어가서, AI가 이 지침을 따르도록 합니다.
# ------------------------------------------------------------
SYSTEM_PROMPT = "너는 따뜻하고 친절한 데이터 분석 선생님이야. 반드시 순수 한국어로만 답해."

# ------------------------------------------------------------
# 5) 세션 상태(session_state)에 대화 기록 저장하기
#    - 스트림릿은 사용자가 메시지를 보낼 때마다 코드를 처음부터 다시 실행합니다.
#    - 그래서 대화 내용을 계속 기억하려면 st.session_state에 저장해야 합니다.
#    - "messages" 라는 이름의 리스트에 지금까지 주고받은 대화를 차곡차곡 쌓습니다.
# ------------------------------------------------------------
if "messages" not in st.session_state:
    # 맨 처음 한 번만 실행됨: 시스템 프롬프트를 대화 기록의 첫 번째로 넣어둡니다.
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# ------------------------------------------------------------
# 6) 지금까지의 대화를 화면에 말풍선으로 그려주기
#    - role이 "system"인 메시지는 사용자에게 보여주지 않습니다(내부 지침이라 숨김).
# ------------------------------------------------------------
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------------------------------------------------
# 7) 사용자 입력창(채팅창) 만들기
#    - st.chat_input()은 화면 하단에 고정된 채팅 입력창을 만들어줍니다.
# ------------------------------------------------------------
user_input = st.chat_input("메시지를 입력하세요...")

if user_input:
    # (1) 사용자가 보낸 메시지를 대화 기록에 추가하고, 화면에도 바로 보여줍니다.
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # (2) AI의 답변을 보여줄 말풍선을 만듭니다.
    with st.chat_message("assistant"):
        # st.empty()는 나중에 내용을 계속 바꿔치기할 수 있는 빈 공간입니다.
        # 스트리밍으로 글자가 실시간으로 나오는 효과를 낼 때 사용합니다.
        placeholder = st.empty()
        full_answer = ""  # AI가 보낸 글자들을 계속 이어 붙일 변수

        try:
            # ------------------------------------------------------------
            # 8) Solar API에 대화 기록 전체를 보내서 답변을 스트리밍으로 받기
            #    - model: 반드시 'solar-open2' 그대로 사용
            #    - stream=True: 답변을 한 번에 받지 않고 조금씩 실시간으로 받음
            #    - reasoning_effort='none': 내부 추론(생각) 과정을 끄고 빠르게 답변
            # ------------------------------------------------------------
            stream = client.chat.completions.create(
                model="solar-open2",
                messages=st.session_state.messages,
                stream=True,
                reasoning_effort="none",
            )

            # (3) 스트리밍으로 오는 조각(chunk)들을 하나씩 받아서 화면에 이어 붙입니다.
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    full_answer += delta.content
                    # 답변 끝에 깜빡이는 커서(▌) 모양을 붙여서 "타이핑 중" 느낌을 줍니다.
                    placeholder.markdown(full_answer + "▌")

            # (4) 스트리밍이 다 끝나면, 커서 없이 최종 답변만 깔끔하게 보여줍니다.
            placeholder.markdown(full_answer)

            # (5) AI의 답변도 대화 기록에 저장해서, 다음 질문에서도 이어서 기억하게 합니다.
            st.session_state.messages.append(
                {"role": "assistant", "content": full_answer}
            )

        except Exception as e:
            # ------------------------------------------------------------
            # 9) 오류(에러)가 나면, 프로그램 에러 화면을 그대로 보여주지 않고
            #    한국어로 친절한 안내 메시지를 대신 보여줍니다.
            # ------------------------------------------------------------
            placeholder.empty()
            st.error(
                "😥 답변을 가져오는 중에 문제가 생겼어요.\n\n"
                "잠시 후 다시 시도해 주세요. "
                "문제가 계속되면 API 키가 올바른지, 인터넷 연결이 안정적인지 확인해 주세요."
            )
            # 방금 실패한 사용자 질문은 대화 기록에서 제거해서,
            # 다음 시도 때 같은 질문을 다시 보낼 수 있게 합니다.
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.pop()
