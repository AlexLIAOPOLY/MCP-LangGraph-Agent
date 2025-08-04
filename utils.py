from typing import Any, Dict, List, Callable, Optional
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
import uuid


def random_uuid():
    return str(uuid.uuid4())


async def astream_graph(
    graph: CompiledStateGraph,
    inputs: dict,
    config: Optional[RunnableConfig] = None,
    node_names: List[str] = [],
    callback: Optional[Callable] = None,
    stream_mode: str = "messages",
    include_subgraphs: bool = False,
) -> Dict[str, Any]:
    """
    异步流式处理LangGraph执行结果并直接输出的函数。

    Args:
        graph (CompiledStateGraph): 要执行的编译后的LangGraph对象
        inputs (dict): 传递给图的输入值字典
        config (Optional[RunnableConfig]): 执行配置（可选）
        node_names (List[str], optional): 要输出的节点名称列表。默认值为空列表
        callback (Optional[Callable], optional): 处理每个数据块的回调函数。默认值为None
            回调函数接收{"node": str, "content": Any}形式的字典作为参数。
        stream_mode (str, optional): 流模式（"messages"或"updates"）。默认值为"messages"
        include_subgraphs (bool, optional): 是否包含子图。默认值为False

    Returns:
        Dict[str, Any]: 最终结果（可选）
    """
    config = config or {}
    final_result = {}

    def format_namespace(namespace):
        return namespace[-1].split(":")[0] if len(namespace) > 0 else "root graph"

    prev_node = ""

    if stream_mode == "messages":
        async for chunk_msg, metadata in graph.astream(
            inputs, config, stream_mode=stream_mode
        ):
            curr_node = metadata["langgraph_node"]
            final_result = {
                "node": curr_node,
                "content": chunk_msg,
                "metadata": metadata,
            }

            # node_names가 비어있거나 현재 노드가 node_names에 있는 경우에만 처리
            if not node_names or curr_node in node_names:
                # 콜백 함수가 있는 경우 실행
                if callback:
                    result = callback({"node": curr_node, "content": chunk_msg})
                    if hasattr(result, "__await__"):
                        await result
                # 콜백이 없는 경우 기본 출력
                else:
                    # 노드가 변경된 경우에만 구분선 출력
                    if curr_node != prev_node:
                        print("\n" + "=" * 50)
                        print(f"🔄 Node: \033[1;36m{curr_node}\033[0m 🔄")
                        print("- " * 25)

                    # Claude/Anthropic 모델의 토큰 청크 처리 - 항상 텍스트만 추출
                    if hasattr(chunk_msg, "content"):
                        # 리스트 형태의 content (Anthropic/Claude 스타일)
                        if isinstance(chunk_msg.content, list):
                            for item in chunk_msg.content:
                                if isinstance(item, dict) and "text" in item:
                                    print(item["text"], end="", flush=True)
                        # 문자열 형태의 content
                        elif isinstance(chunk_msg.content, str):
                            print(chunk_msg.content, end="", flush=True)
                    # 그 외 형태의 chunk_msg 처리
                    else:
                        print(chunk_msg, end="", flush=True)

                prev_node = curr_node

    elif stream_mode == "updates":
        # 错误修复：更改解包方式
        # REACT代理等部分图只返回单一字典
        async for chunk in graph.astream(
            inputs, config, stream_mode=stream_mode, subgraphs=include_subgraphs
        ):
            # 根据返回格式决定处理方法
            if isinstance(chunk, tuple) and len(chunk) == 2:
                # 原有预期格式：(namespace, chunk_dict)
                namespace, node_chunks = chunk
            else:
                # 只返回单一字典的情况（REACT代理等）
                namespace = []  # 空命名空间（根图）
                node_chunks = chunk  # chunk本身就是节点块字典

            # 确认是否为字典并处理项目
            if isinstance(node_chunks, dict):
                for node_name, node_chunk in node_chunks.items():
                    final_result = {
                        "node": node_name,
                        "content": node_chunk,
                        "namespace": namespace,
                    }

                    # 仅在node_names不为空时进行过滤
                    if len(node_names) > 0 and node_name not in node_names:
                        continue

                    # 如果有回调函数则执行
                    if callback is not None:
                        result = callback({"node": node_name, "content": node_chunk})
                        if hasattr(result, "__await__"):
                            await result
                    # 没有回调的情况下默认输出
                    else:
                        # 仅当节点变更时输出分隔线（与messages模式相同）
                        if node_name != prev_node:
                            print("\n" + "=" * 50)
                            print(f"🔄 Node: \033[1;36m{node_name}\033[0m 🔄")
                            print("- " * 25)

                        # 输出节点的块数据 - 以文本为中心处理
                        if isinstance(node_chunk, dict):
                            for k, v in node_chunk.items():
                                if isinstance(v, BaseMessage):
                                    # BaseMessage의 content 속성이 텍스트나 리스트인 경우를 처리
                                    if hasattr(v, "content"):
                                        if isinstance(v.content, list):
                                            for item in v.content:
                                                if (
                                                    isinstance(item, dict)
                                                    and "text" in item
                                                ):
                                                    print(
                                                        item["text"], end="", flush=True
                                                    )
                                        else:
                                            print(v.content, end="", flush=True)
                                    else:
                                        v.pretty_print()
                                elif isinstance(v, list):
                                    for list_item in v:
                                        if isinstance(list_item, BaseMessage):
                                            if hasattr(list_item, "content"):
                                                if isinstance(list_item.content, list):
                                                    for item in list_item.content:
                                                        if (
                                                            isinstance(item, dict)
                                                            and "text" in item
                                                        ):
                                                            print(
                                                                item["text"],
                                                                end="",
                                                                flush=True,
                                                            )
                                                else:
                                                    print(
                                                        list_item.content,
                                                        end="",
                                                        flush=True,
                                                    )
                                            else:
                                                list_item.pretty_print()
                                        elif (
                                            isinstance(list_item, dict)
                                            and "text" in list_item
                                        ):
                                            print(list_item["text"], end="", flush=True)
                                        else:
                                            print(list_item, end="", flush=True)
                                elif isinstance(v, dict) and "text" in v:
                                    print(v["text"], end="", flush=True)
                                else:
                                    print(v, end="", flush=True)
                        elif node_chunk is not None:
                            if hasattr(node_chunk, "__iter__") and not isinstance(
                                node_chunk, str
                            ):
                                for item in node_chunk:
                                    if isinstance(item, dict) and "text" in item:
                                        print(item["text"], end="", flush=True)
                                    else:
                                        print(item, end="", flush=True)
                            else:
                                print(node_chunk, end="", flush=True)

                        # 这里不输出分隔线（与messages模式相同）

                    prev_node = node_name
            else:
                # 非字典情况输出整个块
                print("\n" + "=" * 50)
                print(f"🔄 Raw output 🔄")
                print("- " * 25)
                print(node_chunks, end="", flush=True)
                # 这里不输出分隔线
                final_result = {"content": node_chunks}

    else:
        raise ValueError(
            f"Invalid stream_mode: {stream_mode}. Must be 'messages' or 'updates'."
        )

    # 필요에 따라 최종 결과 반환
    return final_result


async def ainvoke_graph(
    graph: CompiledStateGraph,
    inputs: dict,
    config: Optional[RunnableConfig] = None,
    node_names: List[str] = [],
    callback: Optional[Callable] = None,
    include_subgraphs: bool = True,
) -> Dict[str, Any]:
    """
    异步流式输出LangGraph应用执行结果的函数。

    Args:
        graph (CompiledStateGraph): 要执行的编译后的LangGraph对象
        inputs (dict): 传递给图的输入值字典
        config (Optional[RunnableConfig]): 执行配置（可选）
        node_names (List[str], optional): 要输出的节点名称列表。默认值为空列表
        callback (Optional[Callable], optional): 处理每个数据块的回调函数。默认值为None
            回调函数接收{"node": str, "content": Any}形式的字典作为参数。
        include_subgraphs (bool, optional): 是否包含子图。默认值为True

    Returns:
        Dict[str, Any]: 最终结果（最后一个节点的输出）
    """
    config = config or {}
    final_result = {}

    def format_namespace(namespace):
        return namespace[-1].split(":")[0] if len(namespace) > 0 else "root graph"

    # 通过subgraphs参数也包含子图的输出
    async for chunk in graph.astream(
        inputs, config, stream_mode="updates", subgraphs=include_subgraphs
    ):
        # 根据返回格式决定处理方法
        if isinstance(chunk, tuple) and len(chunk) == 2:
            # 原有预期格式：(namespace, chunk_dict)
            namespace, node_chunks = chunk
        else:
            # 只返回单一字典的情况（REACT代理等）
            namespace = []  # 空命名空间（根图）
            node_chunks = chunk  # chunk本身就是节点块字典

        # 确认是否为字典并处理项目
        if isinstance(node_chunks, dict):
            for node_name, node_chunk in node_chunks.items():
                final_result = {
                    "node": node_name,
                    "content": node_chunk,
                    "namespace": namespace,
                }

                # 仅在node_names不为空时进行过滤
                if node_names and node_name not in node_names:
                    continue

                # 如果有回调函数则执行
                if callback is not None:
                    result = callback({"node": node_name, "content": node_chunk})
                    # 如果是协程则await
                    if hasattr(result, "__await__"):
                        await result
                # 没有回调的情况下默认输出
                else:
                    print("\n" + "=" * 50)
                    formatted_namespace = format_namespace(namespace)
                    if formatted_namespace == "root graph":
                        print(f"🔄 Node: \033[1;36m{node_name}\033[0m 🔄")
                    else:
                        print(
                            f"🔄 Node: \033[1;36m{node_name}\033[0m in [\033[1;33m{formatted_namespace}\033[0m] 🔄"
                        )
                    print("- " * 25)

                    # 输出节点的块数据
                    if isinstance(node_chunk, dict):
                        for k, v in node_chunk.items():
                            if isinstance(v, BaseMessage):
                                v.pretty_print()
                            elif isinstance(v, list):
                                for list_item in v:
                                    if isinstance(list_item, BaseMessage):
                                        list_item.pretty_print()
                                    else:
                                        print(list_item)
                            elif isinstance(v, dict):
                                for node_chunk_key, node_chunk_value in v.items():
                                    print(f"{node_chunk_key}:\n{node_chunk_value}")
                            else:
                                print(f"\033[1;32m{k}\033[0m:\n{v}")
                    elif node_chunk is not None:
                        if hasattr(node_chunk, "__iter__") and not isinstance(
                            node_chunk, str
                        ):
                            for item in node_chunk:
                                print(item)
                        else:
                            print(node_chunk)
                    print("=" * 50)
        else:
            # 非字典情况输出整个块
            print("\n" + "=" * 50)
            print(f"🔄 Raw output 🔄")
            print("- " * 25)
            print(node_chunks)
            print("=" * 50)
            final_result = {"content": node_chunks}

    # 返回最终结果
    return final_result
