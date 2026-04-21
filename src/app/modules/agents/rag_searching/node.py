import json

from langchain.agents import create_agent

from app.core.llm.chains.contract_chains import get_llm_chain
from app.core.llm.factory import get_chat_model
from app.shared.tools.retrieval import rag_retrieve_tool, rag_sammarize_tool
from app.utils.prompt_loader import load_prompt


def _append_step(state: dict, label: str, detail: object | None) -> list[tuple]:
    """在 past_steps 中追加一条记录（不再截断内容）。"""

    past_steps = list(state.get("past_steps", []))
    text = ""
    if detail is not None:
        text = str(detail)
    past_steps.append((label, text))
    return past_steps


def _merge_contract_info(old: dict, new: dict) -> dict:
    """将旧的 contract_info 与本轮新提取结果合并。

    规则：
    - 优先采用新提取的“有效值”（非空、非"未知"/"unknown"），否则保留旧值；
    - special_terms 做合并去重；
    - 根据合并后的结果重新计算 is_complete 与 missing_fields。
    """

    old = old or {}
    new = new or {}
    merged: dict = dict(old)

    # 简单字段合并
    important_fields = [
        "intent",#意图
        "fact",# 事实
        "evidence",
    ]

    def _is_valid(v: object) -> bool:
        if v is None:
            return False
        s = str(v).strip()
        if not s:
            return False
        return s not in {"未知", "unknown"}

    for key, value in new.items():
        if key in important_fields:
            if _is_valid(value):
                merged[key] = value
            else:
                # 否则保留旧值（如果有）
                merged.setdefault(key, value)
        elif key == "special_terms":
            old_terms = merged.get("special_terms") or []
            new_terms = value or []
            if not isinstance(old_terms, list):
                old_terms = [old_terms]
            if not isinstance(new_terms, list):
                new_terms = [new_terms]
            merged["special_terms"] = list({*map(str, old_terms), *map(str, new_terms)})
        elif key == "extra_fields":
            # 额外要素：期望为字典，多轮提取时做浅层合并，新结果优先
            old_extra = merged.get("extra_fields") or {}
            if not isinstance(old_extra, dict):
                old_extra = {"_legacy": old_extra}
            new_extra = value or {}
            if not isinstance(new_extra, dict):
                new_extra = {"_new": new_extra}
            tmp = dict(old_extra)
            tmp.update(new_extra)
            merged["extra_fields"] = tmp
        else:
            # 其他字段以新结果为准
            merged[key] = value

    # 根据合并后的结果重新计算完整性（面向一般法律问题/案件要素，而非仅限合同）
    field_names = {
        "intent": "意图",
        "fact": "事实",
        "evidence": "相关证据",
    }
    missing_fields = []
    for k, label in field_names.items():
        v = merged.get(k)
        if not _is_valid(v):
            missing_fields.append(label)

    merged["missing_fields"] = missing_fields
    merged["is_complete"] = len(missing_fields) == 0

    if not merged.get("reason"):
        if missing_fields:
            merged["reason"] = "未提及" + "、".join(missing_fields)
        else:
            merged["reason"] = "关键信息已基本完整"

    return merged
async def extract_node(state: dict):
    """提取节点：结合历史 contract_info 与本轮输入一起提取并合并。"""

    resp = await get_llm_chain("src/app/modules/agents/rag_searching/input.jinja2").ainvoke(
        {"input": state["input"]}
    )
    content = getattr(resp, "content", str(resp))
    try:
        # 尝试从模型输出中截取纯 JSON（去掉可能的 ```json 代码块包裹）
        text = str(content).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = text[start : end + 1]
        else:
            json_str = text

        extracted_data = json.loads(json_str)
    except json.JSONDecodeError:
        # 当模型未按要求返回合法 JSON 时，避免整个流程崩溃
        print(f"extract_node JSON 解析失败, 原始内容: {content!r}")
        msg = "抱歉，我没能从你的描述中识别出清晰的要求。请尽量说明事实、意图、相关证据等关键信息。"
        past_steps = _append_step(state, "信息提取失败", msg)
        return {
            "contract_info": state.get("contract_info", {}),
            "past_steps": past_steps,
            "response": msg,
        }

    # 与历史 contract_info 合并
    old_info = state.get("contract_info", {}) or {}
    merged_info = _merge_contract_info(old_info, extracted_data)

    is_complete = bool(merged_info.get("is_complete", False))
    missing = merged_info.get("missing_fields", []) or []
    reason = merged_info.get("reason", "未知原因")
    past_steps = _append_step(
        state,
        "信息提取",
        f"已累积识别{len(merged_info)}个字段，信息{'完整' if is_complete else '不完整'}",
    )

    # 若不完整：直接返回缺失字段提示，让调用方提示用户补充后重新输入；
    # 后续节点（add / RAG / write / check）不再继续执行，由图上的条件边控制。
    if not is_complete:
        missing_str = "、".join(str(x) for x in missing) if missing else "若干关键要素"
        reason_str = f"，原因是{reason}" if reason else ""
        msg = f"{reason_str},请补充{missing_str}等关键信息，以便我更好地帮助你分析相关的法律问题。"
        return {
            "contract_info": merged_info,
            "past_steps": past_steps,
            "response": msg,
        }

    # 信息完整：正常进入后续节点
    return {"contract_info": merged_info, "past_steps": past_steps}
async def clarification_node(state: dict):
    # 1. 获取提取节点留下的缺失线索
    info = state.get("contract_info", {})
    missing = info.get("missing_fields", [])
    reason = info.get("reason", "未知原因")
    # 2. 如果没有缺失字段，说明关键信息已基本完整，直接跳过澄清阶段
    #    保留一个简要的 past_steps 记录即可，不再向用户追加“没听懂”这类无意义提示。
    if not missing:
        return {
            "contract_info": info,
            "past_steps": _append_step(state, "信息澄清略过", "关键信息已基本完整，无需澄清。"),
        }

    # 3. 调用澄清链生成追问话术
    msg = await get_llm_chain("src/app/modules/agents/rag_searching/clarification.jinja2").ainvoke({
        "extracted_info": info,
        "missing_fields": missing,
        "reason": reason,
    })
    content = getattr(msg, "content", str(msg))
    new_info = info.copy()
    new_info["legal_context"] = content

    # 4. 把话术存入 response，准备回传给用户
    return {
        "contract_info": new_info,
        "past_steps": _append_step(state, "信息澄清", content),
    }
async def category_node(state: dict):
    info = state.get("contract_info", {})
    # 将当前已提取的要素 JSON 和澄清上下文一起提供给分类模型，
    # 避免只看到追问话术而丢失核心争议（如“故意杀人/过失伤人”）。
    rich_content = {
        "contract_info": info,
        "legal_context": info.get("legal_context", "无澄清信息"),
    }
    content = json.dumps(rich_content, ensure_ascii=False, indent=2)
    # 1. 构建分类提示词，提供当前已提取的要素信息，帮助模型判断应检索的法律类别
    category_llm = get_llm_chain("src/app/modules/agents/rag_searching/ragcategory.jinja2")
    # 2. 调用 Agent 进行分类
    response = await category_llm.ainvoke({"content": content})
    if isinstance(response, dict):
        content = response.get("output", str(response))
    else:
        content = getattr(response, "content", str(response))
    # 4. 安全地更新 State
    new_info = info.copy()
    new_info["categories"] = str(content).strip()
    return {
        "contract_info": new_info,
        "past_steps": _append_step(state, "法律分类", content),
    }
async def retriver_node(state: dict):
    info = state.get("contract_info", {})
    
    # 提前判断：如果没有明确的法律问题类型/案件类型，不浪费 Token
    if not info.get("categories") or info["categories"] == "unknown":
        return {
            "past_steps": _append_step(state, "法律检索", "法律问题类型未知，未执行法律检索。"),
        }

    # 将当前已提取的法律要素/案件要素以 JSON 形式一并提供给检索/模型，
    # 便于其在理解具体场景的前提下做更有针对性的检索与总结。
    info_json = json.dumps(info, ensure_ascii=False, indent=2)
    raw_categories = info.get("categories")

    # categories 可能是 JSON 字符串，也可能已经是列表
    try:
        if isinstance(raw_categories, str):
            categories: list = json.loads(raw_categories)
        else:
            categories: list = raw_categories or []
    except json.JSONDecodeError:
        categories = []

    try:
        retrieved_laws: list[str] = []

        if categories:
            # 按分类结果逐条调用检索工具
            for item in categories:
                if not isinstance(item, dict):
                    continue

                cat_path = item.get("category")
                law_name = item.get("law_name") or info.get("law_name")
                article = item.get("article") or info.get("article")

                # 针对每一条分类结果单独构造检索 query，避免所有条文共用同一段巨大 JSON，
                # 提高按具体条文命中的概率。
                base_intent = str(info.get("intent", "")).strip()
                base_fact = str(info.get("fact", "")).strip()
                # 若缺失条文信息，则退回到整体 JSON 作为 query
                if law_name and article:
                    search_query = "\n".join(
                        part
                        for part in [
                            f"用户问题：{base_intent}" if base_intent else "",
                            f"案件概述：{base_fact}" if base_fact else "",
                            f"检索目标：围绕《{law_name}》{article} 的相关规定，提供与上述问题最相关的法条片段",
                        ]
                        if part
                    )
                else:
                    search_query = info_json

                # rag_retrieve_tool 是同步工具，不能直接 await，这里通过 invoke 调用
                response = rag_retrieve_tool.invoke(
                    {
                        "query": search_query,
                        "category": cat_path,
                        "law_name": law_name,
                        "article": article,
                        "k": 3,
                    }
                )
                retrieved_laws.append(str(response))
        else:
            # 没有分类结果时，退化为单次检索
            response = rag_retrieve_tool.invoke(
                {
                    "query": search_query,
                    "category": None,
                    "law_name": info.get("law_name"),
                    "article": info.get("article"),
                    "k": 3,
                }
            )
            retrieved_laws.append(str(response))

        # 汇总文本，方便后续直接当作上下文使用
        merged_content = "\n\n".join(retrieved_laws) if retrieved_laws else "未找到相关文档。"

        # 4. 安全地更新 State
        new_info = info.copy()
        new_info["retrieved_laws"] = retrieved_laws

        return {
            "contract_info": new_info,
            "past_steps": _append_step(state, "法律检索", f"共检索到 {len(retrieved_laws)} 组相关条文。"),
        }
        
    except Exception as e:
        print(f"检索节点运行失败: {e}")
        return {
            "past_steps": _append_step(state, "法律检索失败", str(e)),
        }
async def generator_node(state: dict):
    """法律科普总结/说明节点：根据已提取信息和法律背景，生成结构化说明文本。"""
    info = state.get("contract_info", {})
    past_steps = state.get("past_steps", [])

    try:
        # 使用本 agent 下的法律科普 summary 提示词构建链（仅用于 rag_searching 场景）
        chain = get_llm_chain("src/app/modules/agents/rag_searching/summary_prompt.jinja2")
        # 直接将当前 contract_info 作为上下文传入（序列化为 JSON 便于模型阅读）
        payload = {"contract_info": json.dumps(info, ensure_ascii=False, indent=2)}
        summary = await chain.ainvoke(payload)

        # 安全更新 State
        new_info = info.copy()
        # 统计写作重试次数，用于在路由中做上限控制
        retry_count = int(new_info.get("retry_count", 0))
        new_info["retry_count"] = retry_count + 1
        new_info["legal_summary"] = summary

        return {
            "contract_info": new_info,
            "past_steps": _append_step(state, "信息总结", summary),
        }

    except Exception as e:
        print(f"总结节点运行失败: {e}")
        return {}
    
async def check_node(state: dict):
    """检查节点：对生成的法律科普说明进行自我检查，确保没有遗漏重要信息或逻辑错误。"""
    info = state.get("contract_info", {})
    past_steps = state.get("past_steps", [])

    try:
        # 使用本 agent 下的检查提示词构建链，面向一般法律科普场景
        chain = get_llm_chain("src/app/modules/agents/rag_searching/contract_check_prompt.jinja2")
        payload = {"contract_info": json.dumps(info, ensure_ascii=False, indent=2)}
        raw = await chain.ainvoke(payload)

        # 将输出转为字符串，并尽可能剥离代码块包装，只保留 JSON 部分
        text = str(raw).strip()
        # 尝试截取第一个 "{" 到 最后一个 "}" 之间的内容，去掉 ```json 代码块等噪声
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = text[start : end + 1]
        else:
            json_str = text

        # 解析检查结果 JSON，确保拿到 is_pass 等结构化信息
        try:
            parsed = json.loads(json_str)
        except Exception:
                parsed = {
                "is_pass": False,
                "issues": ["检查结果解析失败，原始输出：" + text],
                "suggestion": "请人工复核当前法律说明。",
            }

        # 安全更新 State
        new_info = info.copy()
        new_info["check_result"] = parsed

        return {
            "contract_info": new_info,
            "past_steps": _append_step(state, "信息检查", parsed),
        }

    except Exception as e:
        print(f"检查节点运行失败: {e}")
        return {}
async def output_node(state: dict):
    """输出节点：根据 contract_info / legal_summary / check_result 生成最终说明。"""

    info = state.get("contract_info", {}) or {}
    check_result = info.get("check_result", {}) or {}

    # 将前序生成的 summary 统一转成字符串，便于注入模板
    raw_summary = info.get("legal_summary", "")
    legal_summary = getattr(raw_summary, "content", str(raw_summary))

    payload = {
        "contract_info": json.dumps(info, ensure_ascii=False, indent=2),
        "legal_summary": legal_summary,
        "check_result": json.dumps(check_result, ensure_ascii=False, indent=2),
    }

    try:
        chain = get_llm_chain("src/app/modules/agents/rag_searching/output_prompt.jinja2")
        result = await chain.ainvoke(payload)
        content = getattr(result, "content", str(result))

        return {
            "contract_info": info,
            "past_steps": _append_step(state, "最终输出", content),
            "response": content,
        }

    except Exception as e:
        # 回退策略：若最终生成阶段失败，至少返回检查节点的结论，避免整个流程崩溃
        print(f"output_node 运行失败: {e}")
        if check_result.get("is_pass"):
            text = legal_summary or "法律说明生成成功，但最终生成节点出现异常，请人工复核。"
        else:
            issues = check_result.get("issues", ["未知问题"])
            suggestion = check_result.get("suggestion", "请人工复核当前法律说明。")
            text = f"法律说明存在以下问题：{', '.join(issues)}。建议：{suggestion}"

        return {
            "contract_info": info,
            "past_steps": _append_step(state, "最终输出失败", str(e)),
            "response": text,
        }
