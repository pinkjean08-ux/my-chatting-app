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
# 4) 말투(페르소나) 목록 정의
#    - 사이드바에서 고를 수 있는 말투와, 각 말투에 맞는 시스템 프롬프트 문장을 미리 만들어둡니다.
#    - 공통 규칙("반드시 순수 한국어로만 답해")은 모든 말투에 공통으로 붙여줍니다.
# ------------------------------------------------------------
COMMON_RULE = " 반드시 순수 한국어로만 답해."

PERSONAS = {
    "친절한 선생님": "너는 따뜻하고 친절한 데이터 분석 선생님이야." + COMMON_RULE,
    "시크한 전문가": "너는 군더더기 없이 핵심만 딱딱 짚어주는 시크한 데이터 분석 전문가야. 다정한 말투 대신 담백하고 단호한 말투를 써." + COMMON_RULE,
    "귀여운 친구": "너는 이모티콘과 애교 섞인 말투를 쓰는 귀엽고 발랄한 친구야. 어려운 데이터 분석 내용도 쉽고 재미있게 설명해줘." + COMMON_RULE,
}

# ------------------------------------------------------------
# 5) 사이드바 UI 만들기
#    - '말투 고르기' 라디오 버튼과 '대화 지우기' 버튼을 넣습니다.
# ------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 설정")

    # 라디오 버튼으로 말투를 고릅니다. 선택값은 st.session_state.persona_name에 저장됩니다.
    selected_persona = st.radio(
        "말투 고르기",
        options=list(PERSONAS.keys()),
        key="persona_name",
    )

    st.divider()

    # '대화 지우기' 버튼: 누르면 세션에 쌓인 대화 기록을 모두 비웁니다.
    if st.button("🗑️ 대화 지우기", use_container_width=True):
        st.session_state.messages = []  # 대화 기록을 완전히 비웁니다.
        st.rerun()  # 화면을 새로고침해서 비워진 상태를 바로 반영합니다.

# ------------------------------------------------------------
# 6) 세션 상태(session_state)에 대화 기록 저장하기
#    - 스트림릿은 사용자가 메시지를 보낼 때마다 코드를 처음부터 다시 실행합니다.
#    - 그래서 대화 내용을 계속 기억하려면 st.session_state에 저장해야 합니다.
#    - "messages" 리스트에는 사용자/AI가 주고받은 대화만 저장하고(user, assistant),
#      시스템 프롬프트는 API로 보낼 때 맨 앞에 따로 붙여줍니다.
#      (이렇게 하면 말투를 바꿔도 이미 나눈 대화 기록은 그대로 남고,
#       다음 답변부터 새 말투가 바로 적용됩니다.)
# ------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------------------------------------------------
# 7) 지금까지의 대화를 화면에 말풍선으로 그려주기
# ------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------------------------------------------------
# 8) 사용자 입력창(채팅창) 만들기
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
            # 현재 사이드바에서 선택된 말투에 맞는 시스템 프롬프트를 가져옵니다.
            # 매번 이 시점에 새로 가져오기 때문에, 대화 중간에 말투를 바꿔도
            # 다음 질문부터는 바로 새 말투가 적용됩니다.
            current_system_prompt = PERSONAS[st.session_state.persona_name]

            # API에 보낼 메시지 목록: [시스템 프롬프트] + [지금까지의 대화 기록]
            messages_to_send = (
                [{"role": "system", "content": current_system_prompt}]
                + st.session_state.messages
            )

            # ------------------------------------------------------------
            # 9) Solar API에 대화 기록 전체를 보내서 답변을 스트리밍으로 받기
            #    - model: 반드시 'solar-open2' 그대로 사용
            #    - stream=True: 답변을 한 번에 받지 않고 조금씩 실시간으로 받음
            #    - reasoning_effort='none': 내부 추론(생각) 과정을 끄고 빠르게 답변
            # ------------------------------------------------------------
            stream = client.chat.completions.create(
                model="solar-open2",
                messages=messages_to_send,
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
            # 10) 오류(에러)가 나면, 프로그램 에러 화면을 그대로 보여주지 않고
            #     한국어로 친절한 안내 메시지를 대신 보여줍니다.
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
