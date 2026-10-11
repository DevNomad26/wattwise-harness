import json
import uuid
import sys
import os
import inspect
from contextlib import AsyncExitStack
from typing import List, Dict, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from wattwise.models import OllamaClient
from wattwise.schemas import Step
from wattwise.adapter import parse_step_json, match_tool_name
from wattwise.skills_loader import get_all_skills, load_skill

MISSING_TOOL_NAMES = {"", "null", "none"}

def skill_for_tool(tool_name: str | None, tool_names: List[str], skill_names: List[str]) -> str | None:
    """Small models often call a skill by name as if it were a tool. Return that skill's name."""
    if not tool_name or tool_name in tool_names or tool_name == "load_skill":
        return None
    matched = match_tool_name(tool_name, skill_names)
    return matched if matched in skill_names else None

class AgentLoop:
    def __init__(self, model_name: str = "qwen3.5:4b"):
        # Localhost by default
        ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.model = OllamaClient(model_name=model_name, host=ollama_host)
        
    async def run(self, user_prompt: str, mcp_scripts: List[str], history: List[Dict[str, str]] | None = None, on_event = None) -> str:
        """Run one question. `history` holds earlier non-system messages so follow-up
        questions can reuse earlier tool results; after the run, self.messages holds the
        full transcript."""
        async def emit(event_type: str, data: dict):
            if on_event:
                try:
                    res = on_event(event_type, data)
                    if inspect.isawaitable(res):
                        await res
                except Exception:
                    pass

        run_id = str(uuid.uuid4())
        print(f"\nStarting run {run_id}")
        await emit("start", {"prompt": user_prompt})

        messages = [
            {
                "role": "system",
                "content": "You are a smart energy assistant. Always reply with strict JSON matching the Step schema. "
                           "If you need to use a tool, set action='tool', provide tool_name and tool_args. "
                           "If you have the final answer, set action='final' and provide final_answer. "
                           "Earlier messages in this conversation and their tool results are still valid; reuse them instead of calling the same tools again."
            },
            *(history or []),
            {"role": "user", "content": user_prompt}
        ]
        self.messages = messages
        
        async with AsyncExitStack() as stack:
            available_tools = {}
            active_sessions = {}
            
            # 0. Inject available skills into the system prompt
            skills = get_all_skills()
            if skills:
                skills_str = "\n".join([f"- {s['name']}: {s['description']}" for s in skills])
                messages[0]["content"] += f"\n\nYou have access to these internal skills:\n{skills_str}\n"
                messages[0]["content"] += "Use the tool 'load_skill' with args {'name': 'skill-name'} to read the full instructions for a skill.\n"
            
            # 1. Connect to all MCP servers
            for script in mcp_scripts:
                server_params = StdioServerParameters(
                    command=sys.executable,
                    args=[script],
                    env=os.environ.copy()
                )
                
                try:
                    transport = await stack.enter_async_context(stdio_client(server_params))
                    read, write = transport
                    session = await stack.enter_async_context(ClientSession(read, write))
                    await session.initialize()
                    
                    tools_response = await session.list_tools()
                    for tool in tools_response.tools:
                        available_tools[tool.name] = {
                            "session": session,
                            "schema": {
                                "name": tool.name,
                                "description": tool.description,
                                "input_schema": getattr(tool, 'inputSchema', getattr(tool, 'input_schema', {}))
                            }
                        }
                    print(f"Connected to MCP server: {script}")
                    active_sessions[script] = session
                except Exception as e:
                    print(f"Failed to connect to MCP server {script}: {e}")
            
            # We inject available tools into the system prompt conceptually exactly ONCE
            tools_list = [v["schema"] for v in available_tools.values()]
            if tools_list:
                tools_str = json.dumps(tools_list, indent=2)
                messages[0]["content"] += f"\n\nAvailable tools:\n{tools_str}"
                
            # 2. Main agent loop (max 8 steps)
            for step_idx in range(1, 9):
                print(f"Step {step_idx}/8")
                await emit("step_start", {"step": step_idx, "max_steps": 8})
                
                # Get model response
                response = await self.model.generate(messages)
                raw_content = response["content"]
                
                # Check for Thinking Controller Failsafe interception
                if raw_content.startswith("<CUTOFF>"):
                    print(f"Intercepted stuck reasoning: {raw_content}")
                    messages.append({"role": "assistant", "content": '{"action": "tool", "tool_name": "think_failsafe", "tool_args": {}}'})
                    messages.append({"role": "user", "content": "You are repeating yourself or taking too long. Please answer now without thinking."})
                    continue
                
                try:
                    response_data = parse_step_json(raw_content)
                    step = Step(**response_data)
                except Exception as e:
                    print(f"Failed to parse model output: {e}")
                    messages.append({"role": "assistant", "content": raw_content})
                    messages.append({"role": "user", "content": "Failed to parse JSON matching Step schema. Try again."})
                    continue
                    
                messages.append({"role": "assistant", "content": step.model_dump_json()})
                
                if step.thought:
                    print(f"Thought: {step.thought}")
                    await emit("thought", {"step": step_idx, "thought": step.thought})
                
                if step.action == "final":
                    print("Final answer reached.")
                    await emit("final_answer", {"step": step_idx, "answer": step.final_answer})
                    return step.final_answer
                    
                elif step.action == "tool":
                    if str(step.tool_name or "").strip().lower() in MISSING_TOOL_NAMES:
                        print("Model sent a tool call without a tool name.")
                        messages.append({"role": "user", "content": "No tool_name given. If you have the answer, reply with action='final' and put it in final_answer."})
                        continue

                    skill = skill_for_tool(step.tool_name, list(available_tools.keys()), [s["name"] for s in skills])
                    if skill:
                        step.tool_name, step.tool_args = "load_skill", {"name": skill}

                    await emit("tool_call", {
                        "step": step_idx,
                        "tool": step.tool_name,
                        "args": step.tool_args or {},
                        "thought": step.thought,
                    })

                    # Internal Tool: load_skill
                    if step.tool_name == "load_skill":
                        skill_name = step.tool_args.get("name") if step.tool_args else None
                        print(f"Calling internal tool load_skill with name '{skill_name}'")
                        if not skill_name:
                            messages.append({"role": "user", "content": "Missing 'name' argument for load_skill."})
                            continue
                        skill_content = load_skill(skill_name)
                        messages.append({"role": "user", "content": f"Loaded Skill '{skill_name}':\n{skill_content}"})
                        await emit("tool_result", {
                            "step": step_idx,
                            "tool": "load_skill",
                            "result": f"Loaded skill '{skill_name}'"
                        })
                        continue

                    # External MCP Tools
                    if step.tool_name:
                        step.tool_name = match_tool_name(step.tool_name, list(available_tools.keys()))
                        
                    if not step.tool_name or step.tool_name not in available_tools:
                        error_msg = f"Tool '{step.tool_name}' not found."
                        print(error_msg)
                        messages.append({"role": "user", "content": error_msg})
                        continue
                        
                    print(f"Calling tool {step.tool_name} with {step.tool_args}")
                    session = available_tools[step.tool_name]["session"]
                    
                    try:
                        tool_result = await session.call_tool(step.tool_name, step.tool_args or {})
                        result_text = "\n".join([c.text for c in tool_result.content])
                        messages.append({
                            "role": "user", 
                            "content": f"Tool '{step.tool_name}' returned:\n{result_text}"
                        })
                        await emit("tool_result", {
                            "step": step_idx,
                            "tool": step.tool_name,
                            "result": result_text[:500]
                        })
                    except Exception as e:
                        print(f"Tool execution failed: {e}")
                        messages.append({"role": "user", "content": f"Tool execution failed: {e}"})
                        await emit("tool_result", {
                            "step": step_idx,
                            "tool": step.tool_name,
                            "result": f"Failed: {e}"
                        })
                
                else:
                    messages.append({"role": "user", "content": "Invalid action. Must be 'tool' or 'final'."})
            
            return "Failed to reach final answer within 8 steps."
