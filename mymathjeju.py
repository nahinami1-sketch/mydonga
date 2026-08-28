import os
import sys
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import streamlit as st

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool

# Windows 콘솔 UTF-8 인코딩 안전 설정
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# .env 환경 변수 로드
load_dotenv()


# =========================================================
# 1. Pydantic BaseModel 상속 입력 스키마 정의
# =========================================================
class MathQuery(BaseModel):
    """수학 연산 정보를 정의하는 입력 스키마"""
    operation: str = Field(
        ..., 
        description="수행할 연산 종류 ('add', 'subtract', 'multiply', 'divide', 'abs' 또는 '+', '-', '*', '/', '절댓값' 등)"
    )
    num1: float = Field(..., description="첫 번째 숫자")
    num2: float = Field(default=0.0, description="두 번째 숫자")

    def calculate(self) -> float:
        """연산을 수행하고 결과를 반환하는 메서드"""
        op = self.operation.lower().strip()
        if op in ["add", "+", "더하기", "plus", "합"]:
            return self.num1 + self.num2
        elif op in ["subtract", "-", "빼기", "minus", "차"]:
            return self.num1 - self.num2
        elif op in ["multiply", "*", "x", "곱하기", "times", "곱"]:
            return self.num1 * self.num2
        elif op in ["divide", "/", "나누기", "div", "몫"]:
            if self.num2 == 0:
                raise ValueError("0으로 나눌 수 없습니다.")
            return self.num1 / self.num2
        elif op in ["abs", "절댓값", "절대값"]:
            # 두 번째 인자가 0이 아니면 두 수의 차이의 절댓값, 그렇지 않으면 num1의 절댓값
            if self.num2 != 0.0:
                return abs(self.num1 - self.num2)
            return abs(self.num1)
        else:
            raise ValueError(f"지원하지 않는 연산 타입입니다: '{self.operation}'. (사용 가능: add, subtract, multiply, divide, abs)")


class JejuQuery(BaseModel):
    """제주도 정보(날씨, 관광지, 특산물/맛집, 여행팁) 조회를 위한 입력 스키마"""
    category: str = Field(
        ..., 
        description="조회할 제주 정보 카테고리 ('weather', 'tourist_spot', 'food', 'tip' 또는 '날씨', '관광지', '맛집', '여행팁')"
    )
    location: str = Field(default="제주도 전체", description="조회할 제주 세부 지역 (예: 서귀포, 애월, 성산, 제주시)")
    date: Optional[str] = Field(default="today", description="조회할 날짜 (예: 오늘, 내일, YYYY-MM-DD)")

    def get_jeju_info(self) -> str:
        """제주 요청 카테고리에 맞는 요약 정보를 반환하는 메서드"""
        cat = self.category.lower().strip()
        date_str = self.date if self.date else "오늘"
        loc_str = self.location if self.location else "제주도 전체"

        if cat in ["weather", "날씨", "기상", "일기예보"]:
            return f"🌤️ [{loc_str}] {date_str} 날씨: 맑음, 기온: 22°C, 강수확률: 10% (여행하기 좋은 쾌청한 날씨입니다)"
        elif cat in ["tourist_spot", "tourist", "spot", "관광지", "관광", "명소", "여행지", "추천지"]:
            return f"🌋 [{loc_str}] 대표 추천 관광지: 성산일출봉, 섭지코지, 한라산 국립공원, 곽지해수욕장, 협재해변"
        elif cat in ["food", "restaurant", "맛집", "특산물", "음식", "먹거리", "식당"]:
            return f"🍊 [{loc_str}] 추천 특산물 및 맛집: 흑돼지 구이, 제주 감귤/한라봉, 고기국수, 갈치조림, 옥돔구이"
        elif cat in ["tip", "travel_tip", "여행팁", "팁", "꿀팁", "주의사항"]:
            return f"💡 [{loc_str}] 제주 여행 팁: 렌터카 사전 예약 필수, 해안도로 드라이브 추천, 일몰 시간 확인, 날씨 변화 대비 겉옷 지참"
        else:
            return f"🏝️ [{loc_str}] 제주도 맞춤 정보: 제주 여행 가이드 안내가 완료되었습니다. (요청 카테고리: {self.category})"


# =========================================================
# 2. @tool 데코레이터 적용 (args_schema 인자 활용)
# =========================================================
@tool(args_schema=MathQuery)
def math_tool(operation: str, num1: float, num2: float = 0.0) -> str:
    """수학 계산을 수행하는 툴입니다. ('add', 'subtract', 'multiply', 'divide', 'abs' 연산 지원)"""
    query = MathQuery(operation=operation, num1=num1, num2=num2)
    result = query.calculate()
    return f"계산 결과 ({operation}): {result}"


@tool(args_schema=JejuQuery)
def jeju_tool(category: str, location: str = "제주도 전체", date: Optional[str] = "today") -> str:
    """제주도의 날씨, 관광지, 특산물/맛집, 여행 팁 정보를 제공하는 전용 툴입니다."""
    query = JejuQuery(category=category, location=location, date=date)
    return query.get_jeju_info()


# =========================================================
# 3. 툴 리스트 및 딕셔너리 구성
# =========================================================
tools = [math_tool, jeju_tool]
tools_dict = {t.name: t for t in tools}


# =========================================================
# 4. Streamlit UI 및 세션(Session State) 관리
# =========================================================
st.set_page_config(
    page_title="🏝️ 제주 여행 & 수학 스마트 AI 어시스턴트",
    page_icon="🍊",
    layout="wide"
)

# 세션 상태 초기화 (st.session_state)
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 사이드바 (Sidebar) 구성
st.sidebar.title("⚙️ 세션 & 모델 설정")
st.sidebar.markdown("---")

# OpenRouter API 키 상태 확인
api_key = os.getenv("OPENROUTER_API_KEY")
if api_key:
    st.sidebar.success("🔑 OpenRouter API 연결됨")
else:
    st.sidebar.error("⚠️ OPENROUTER_API_KEY를 .env에서 찾을 수 없습니다.")

# 대화 세션 초기화 버튼
if st.sidebar.button("🗑️ 대화 기록 초기화 (Clear Session)", use_container_width=True):
    st.session_state["messages"] = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.metric("💬 현재 세션 대화 수", f"{len(st.session_state['messages'])}개")

# 모델 파라미터 설정
temperature = st.sidebar.slider("Temperature (창의성)", min_value=0.0, max_value=1.0, value=0.0, step=0.1)

st.sidebar.markdown("---")
st.sidebar.subheader("💡 빠른 질문 예시")
preset_query = ""
if st.sidebar.button("🌤️ 제주도 오늘 날씨 알려줘", use_container_width=True):
    preset_query = "제주도 오늘 날씨 알려줘"
if st.sidebar.button("🍊 서귀포 대표 맛집 특산물 추천해줘", use_container_width=True):
    preset_query = "서귀포 대표 맛집 특산물 추천해줘"
if st.sidebar.button("🔢 abs(2 - 17) 계산해줘", use_container_width=True):
    preset_query = "abs(2 - 17) 계산해줘"


# =========================================================
# 5. LCEL 파이프라인 구축 (Prompt | Model | ExecuteTool)
# =========================================================
@st.cache_resource
def get_lcel_chain(temp: float):
    current_key = os.getenv("OPENROUTER_API_KEY")
    if not current_key:
        raise ValueError("OPENROUTER_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인해 주세요.")

    model = ChatOpenAI(
        model="openai/gpt-4o-mini",
        openai_api_key=current_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=temp
    )
    model_with_tools = model.bind_tools(tools)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 제주도 여행 및 수학 연산 도구를 활용하여 사용자의 질문에 정확하고 친절하게 답변하는 AI 가이드입니다. 날씨/맛집/관광지/여행팁이나 수학 계산 요청 시 적절한 도구(math_tool, jeju_tool)를 적극적으로 호출하세요."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{question}")
    ])
    
    def execute_tool_calls(ai_message) -> str:
        if not hasattr(ai_message, "tool_calls") or not ai_message.tool_calls:
            return ai_message.content if hasattr(ai_message, "content") else str(ai_message)

        results = []
        for tool_call in ai_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            target_tool = tools_dict.get(tool_name)
            if target_tool:
                try:
                    output = target_tool.invoke(tool_args)
                    results.append(f"✅ [{tool_name} 호출 성공]\n- 인자: `{tool_args}`\n- 실행 결과: **{output}**")
                except Exception as tool_err:
                    results.append(f"⚠️ [{tool_name} 실행 오류]: {str(tool_err)}")
            else:
                results.append(f"❌ [{tool_name}] 존재하지 않는 툴입니다.")
        return "\n\n".join(results)

    return prompt | model_with_tools | execute_tool_calls


# 메인 화면 구성
st.title("🏝️ 제주 여행 & 수학 AI 어시스턴트")
st.caption("mymathjeju_structure.md 아키텍처 기반: Pydantic + LangChain LCEL + OpenRouter API + Streamlit Session")

# 이전 대화 출력
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력 받기
user_input = st.chat_input("질문을 입력하세요... (예: 제주도 서귀포 특산물 알려줘, abs(2 - 17) 계산해줘)")
if preset_query:
    user_input = preset_query

if user_input:
    # 1. 사용자 질문을 세션 상태에 추가 및 화면 출력
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. 세션 대화 기록을 LangChain 메시지 객체로 변환
    chat_history = []
    for m in st.session_state["messages"][:-1]:
        if m["role"] == "user":
            chat_history.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            chat_history.append(AIMessage(content=m["content"]))

    # 3. AI 답변 생성 및 세션 업데이트
    with st.chat_message("assistant"):
        with st.spinner("LCEL 체인에서 툴을 실행 중입니다..."):
            try:
                lcel_chain = get_lcel_chain(temperature)
                response = lcel_chain.invoke({
                    "question": user_input,
                    "chat_history": chat_history
                })
                st.markdown(response)
                st.session_state["messages"].append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"❌ 오류가 발생했습니다: {str(e)}"
                st.error(error_msg)
                st.session_state["messages"].append({"role": "assistant", "content": error_msg})
