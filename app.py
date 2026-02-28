import time
import uuid
import streamlit as st

from agent.react_agent import ReactAgent

# 标题
st.title("智扫通机器人智能客服")
st.divider()

# 初始化 session_id（用于 checkpointer 持久化）
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

# 初始化 agent
if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()

# 加载历史消息（从 checkpointer）
if "message" not in st.session_state:
    st.session_state["message"] = []

# 显示历史消息
for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

# 用户输入提示词
prompt = st.chat_input()

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    response_messages = []
    with st.spinner("智能客服思考中..."):
        # 使用 session_id 进行会话持久化
        res_stream = st.session_state["agent"].execute_stream(
            prompt,
            session_id=st.session_state["session_id"]
        )

        def capture(generator, cache_list):
            for chunk in generator:
                cache_list.append(chunk)

                for char in chunk:
                    time.sleep(0.01)
                    yield char

        st.chat_message("assistant").write_stream(
            capture(res_stream, response_messages)
        )

        # 保存 assistant 的回复
        if response_messages:
            st.session_state["message"].append(
                {"role": "assistant", "content": response_messages[-1]}
            )

    st.rerun()
