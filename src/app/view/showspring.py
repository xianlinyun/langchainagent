import streamlit as st
import requests
import json

# 配置页面
st.set_page_config(page_title="合同分析助手", layout="centered")

st.title("📄 合同 AI 分析")
st.markdown("请输入合同详情，AI 将为您实时分析合同风险。")

# --- 侧边栏配置 ---
with st.sidebar:
    st.header("服务配置")
    backend_url = st.text_input("后端接口地址", value="https://frp-gap.com:54279/api/contract_analysis_stream")

# --- 表单输入 ---
with st.form("contract_form"):
    col1, col2 = st.columns(2)
    with col1:
        contract_type = st.selectbox("合同类型", ["技术服务协议", "劳动合同", "租赁合同", "采购合同"])
        party_a = st.text_input("甲方名称", value="某某科技有限公司")
        party_b = st.text_input("乙方名称", value="张三")
    with col2:
        amount = st.text_input("金额", value="10000")
        duration = st.text_input("期限", value="3个月")
    
    submitted = st.form_submit_button("开始分析")

# --- 流式展示区域 ---
if submitted:
    payload = {
        "contract_type": contract_type,
        "party_a": party_a,
        "party_b": party_b,
        "amount": amount,
        "duration": duration
    }

    st.subheader("分析结果：")
    # 创建一个空容器用于放置流式文本
    output_container = st.empty()
    full_response = ""

    try:
        # 发送 POST 请求并开启流式接收（对齐 curl: -k -X POST -H "Content-Type: application/json" -d '{...}'）
        with requests.post(
            backend_url,
            data=json.dumps(payload, ensure_ascii=False),
            headers={"Content-Type": "application/json"},
            stream=True,
            verify=False,  # 等价于 curl 的 -k，忽略自签名证书
            timeout=300,
        ) as response:
            if response.status_code != 200:
                st.error(f"服务器错误: {response.status_code}")
            else:
                # 迭代处理 SSE 流
                for line in response.iter_lines():
                    if line:
                        # 解码字节流
                        decoded_line = line.decode('utf-8')
                        
                        # SSE 标准格式以 "data:" 开头
                        if decoded_line.startswith("data:"):
                            json_str = decoded_line[5:].strip()
                            
                            try:
                                # 解析后端传来的 JSON 数据
                                data = json.loads(json_str)
                                token = data.get("content", "")
                                
                                # 拼接并更新 UI
                                full_response += token
                                # 使用 Markdown 渲染，并添加模拟光标
                                output_container.markdown(full_response + "▌")
                            except json.JSONDecodeError:
                                # 忽略非 JSON 格式的干扰行
                                continue
                
                # 渲染最终结果（移除光标）
                output_container.markdown(full_response)
                st.success("分析完成！")

    except Exception as e:
        st.error(f"连接失败: {str(e)}")

# --- 样式优化 ---
# 修正点：将 unsafe_allow_stdio 改为 unsafe_allow_html
st.markdown("""
<style>
    .stAlert { margin-top: 20px; }
    code { white-space: pre-wrap !important; }
</style>
""", unsafe_allow_html=True)