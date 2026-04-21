import time
import uuid
import asyncio
import streamlit as st
from langserve import RemoteRunnable

# --- 核心配置：解耦 Agent 路由 ---
# 本地开发建议直接走宿主机 Nginx：http://localhost
# RemoteRunnable 期望的是 LangServe 应用的基础路径（不需要手动拼 /invoke 或 /stream）。
AGENT_REGISTRY = {
    "合同解释专家": "https://frp-gap.com:54279/api/contract_analysis_stream",
    "法律检索助手": "https://frp-gap.com:54279/api/exchange_analysis_stream",
}

st.set_page_config(page_title="法影智芒", layout="wide")
st.title("法影智芒 - 法律 AI 协作平台")

# --- 会话状态管理 (Session State) ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 侧边栏：多智能体切换与会话重置 ---
with st.sidebar:
    st.header("控制面板")
    
    selected_agent = st.selectbox(
        "切换智能体:",
        options=list(AGENT_REGISTRY.keys()),
        help="基于 LangServe 的动态路由切换"
    )
    
    # 动态实例化远程调用对象
    st.session_state.agent = RemoteRunnable(AGENT_REGISTRY[selected_agent])
    
    if st.button("开启新对话"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.caption(f"Thread ID: `{st.session_state.thread_id}`")

# --- 对话界面渲染 ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 交互逻辑 ---
prompt = st.chat_input("请输入咨询内容...")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Agent 正在执行节点流转..."):
            try:
                async def _run_agent_async(user_input: str, thread_id: str):
                    events = st.session_state.agent.astream_events(
                        {"input": user_input},
                        config={
                            "configurable": {
                                "thread_id": thread_id,
                                "recursion_limit": 50,
                            }
                        },
                        version="v1",
                    )

                    result_state_inner = None
                    async for event in events:
                        if event.get("event") == "on_chain_end":
                            result_state_inner = event.get("data", {}).get("output")

                    return result_state_inner

                # 优先使用基于事件的异步流式调用（对应服务端 astream_events）
                result_state = asyncio.run(
                    _run_agent_async(prompt, st.session_state.thread_id)
                )

                # 兜底：若事件流未能解析出最终状态，则退回一次性 invoke
                if result_state is None:
                    result_state = st.session_state.agent.invoke(
                        {"input": prompt},
                        config={
                            "configurable": {
                                "thread_id": st.session_state.thread_id,
                                "recursion_limit": 50,
                            }
                        },
                    )

                # 结果解析：兼容不同节点的输出结构 (Response/Output)
                state_for_view = result_state
                # LangServe 事件流有时会在外面再包一层 output/metadata，这里做一次解包
                if (
                    isinstance(state_for_view, dict)
                    and "output" in state_for_view
                    and isinstance(state_for_view["output"], dict)
                ):
                    inner = state_for_view["output"]
                    # 如果内层包含典型的工作流字段，则认为内层才是实际状态
                    if any(k in inner for k in ("response", "contract_info", "past_steps")):
                        state_for_view = inner

                if isinstance(state_for_view, dict):
                    answer = (
                        state_for_view.get("response")
                        or state_for_view.get("output")
                        or str(state_for_view)
                    )
                else:
                    answer = str(state_for_view)

                # 若后端为 LangGraph 工作流，则在 state 中会累积 past_steps
                steps = []
                if isinstance(state_for_view, dict) and "past_steps" in state_for_view:
                    steps = state_for_view.get("past_steps") or []

                # 过滤掉噪声较大的中间步骤：信息提取 / 信息澄清略过
                if steps:
                    steps = [
                        (label, detail)
                        for label, detail in steps
                        if label not in ("信息提取", "信息澄清略过")
                    ]

                # 确保 answer 一定是字符串，避免字典被当作可迭代导致 key 拼接在一起
                if not isinstance(answer, str):
                    answer = str(answer)
                
                # 模拟 Token 流式渲染效果
                for chunk in answer:
                    full_response += chunk
                    time.sleep(0.005)
                    placeholder.markdown(full_response + "▌")

                placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

                # 在可折叠区域中展示「思考链路 / 执行节点」
                if steps:
                    with st.expander("查看思考链路 (Node Traces)", expanded=False):
                        for step in steps:
                            # 兼容 (label, detail) 或其他结构
                            if isinstance(step, (list, tuple)) and len(step) >= 2:
                                label, detail = step[0], step[1]
                            else:
                                label, detail = "节点", step

                            st.markdown(f"📍 **节点**: `{label}`")
                            st.caption(str(detail))
                            st.divider()

            except Exception as e:
                st.error(f"Agent 调用异常: {e}")
                st.info("排查建议：检查远程端口 22314 是否放行或后端路由挂载路径是否正确。")