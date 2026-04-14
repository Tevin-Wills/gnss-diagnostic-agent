"""
ReAct Agent for GNSS Multimodal Diagnostics (Session 9).

Implements the Perceive -> Reason -> Act -> Observe loop with:
  - ReAct pattern (Thought / Action / Observation interleaving)
  - Tool calling via structured JSON
  - Guardrails (max iterations, input validation, confidence checks)
  - Short-term memory for state tracking across iterations
  - Full trace logging for evaluation and reporting
"""
import json
import time

import config as cfg
from tools import get_tool_schemas, execute_tool


# ── Agent System Prompt ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a GNSS Diagnostic Agent — an AI-powered engineering assistant
that analyzes GNSS (Global Navigation Satellite System) data from engineering diagrams
to diagnose positioning quality issues in degraded environments.

## Your Role
You receive a diagnostic task and use your tools to:
1. Extract structured data from GNSS engineering visuals (sky plots, DOP tables, C/N0 charts)
2. Analyze the extracted data to identify positioning quality issues
3. Generate a comprehensive diagnostic report with findings and recommendations

## Your Tools
{tool_descriptions}

## ReAct Protocol
You MUST follow the ReAct (Reason + Act) pattern for every step:

1. **Thought**: Reason about the current state. What do you know? What do you need? What should you do next?
2. **Action**: Call exactly ONE tool with specific parameters.
3. **Observation**: You will receive the tool's result. Use it to inform your next Thought.

## Output Format
At each step, respond with EXACTLY this JSON structure:
{{
    "thought": "Your reasoning about the current state and next step",
    "action": {{
        "tool": "tool_name",
        "parameters": {{
            "param1": "value1"
        }}
    }}
}}

When you have completed the task and generated the final report, respond with:
{{
    "thought": "Your final reasoning summarizing what was accomplished",
    "action": {{
        "tool": "TASK_COMPLETE",
        "parameters": {{}}
    }},
    "final_answer": "Brief summary of the diagnostic findings"
}}

## Required Workflow (follow this exact order)
1. Call extract_diagram_data for EACH available diagram (sky_plot, dop_table, cn0_chart)
2. Call analyze_positioning_quality with the extracted data
3. Call generate_diagnostic_report with the analysis findings
4. Call TASK_COMPLETE only AFTER generate_diagnostic_report has been called

## Rules
- You MUST call generate_diagnostic_report before TASK_COMPLETE
- Validate extraction results and note any issues
- If an extraction fails, note the failure and continue with available data
- NEVER fabricate data — only use data from tool results
- Return ONLY valid JSON — no markdown, no explanation, no extra text outside the JSON
"""


def _format_tool_descriptions(schemas: list) -> str:
    """Format tool schemas into a readable string for the system prompt."""
    lines = []
    for schema in schemas:
        lines.append(f"### {schema['name']}")
        lines.append(f"Description: {schema['description']}")
        lines.append(f"Parameters: {json.dumps(schema['parameters'], indent=2)}")
        lines.append("")
    return "\n".join(lines)


class GNSSDiagnosticAgent:
    """ReAct agent for GNSS multimodal diagnostics."""

    def __init__(self):
        self.tool_schemas = get_tool_schemas()
        self.trace = []          # Full Thought/Action/Observation log
        self.memory = {}         # Short-term memory (accumulated results)
        self.iteration = 0
        self.total_latency = 0
        self.start_time = None

    def run(self, task: str, available_images: dict) -> dict:
        """
        Execute the agent loop on a diagnostic task.

        Args:
            task: Natural language description of the diagnostic task.
            available_images: Dict mapping diagram_type -> image_path.

        Returns:
            dict with trace, final report, and evaluation metrics.
        """
        self.start_time = time.time()
        self.trace = []
        self.memory = {
            "task": task,
            "available_images": available_images,
            "extraction_results": [],
            "analysis_result": None,
            "report": None,
        }
        self.iteration = 0

        # Build system prompt with tool descriptions
        tool_desc = _format_tool_descriptions(self.tool_schemas)
        system_prompt = SYSTEM_PROMPT.format(tool_descriptions=tool_desc)

        # Build initial user message with the task
        image_list = "\n".join(f"  - {dtype}: {path}" for dtype, path in available_images.items())
        user_message = (
            f"## Diagnostic Task\n{task}\n\n"
            f"## Available GNSS Diagrams\n{image_list}\n\n"
            f"Begin your diagnostic process. Extract data from each available diagram, "
            f"analyze the results, and generate a comprehensive report."
        )

        # Conversation context for multi-turn
        conversation = [
            {"role": "user", "parts": [f"{system_prompt}\n\n{user_message}"]}
        ]

        # ── Pre-extract all diagrams (deterministic, no LLM needed) ────
        # Small local LLMs often skip diagrams, so we extract all upfront.
        for dtype, path in available_images.items():
            self.iteration += 1
            step_start = time.time()
            action = {"tool": "extract_diagram_data",
                      "parameters": {"image_path": path, "diagram_type": dtype}}
            observation = execute_tool("extract_diagram_data",
                                       {"image_path": path, "diagram_type": dtype})
            self._log_step(
                f"Extracting structured data from {dtype} diagram.",
                action, observation, time.time() - step_start)
            self._update_memory("extract_diagram_data", observation)

        # ── Run analysis on all extracted data ─────────────────────────
        self.iteration += 1
        step_start = time.time()
        analysis_params = {}
        if self.memory.get("satellite_data"):
            analysis_params["satellite_data"] = self.memory["satellite_data"]
        if self.memory.get("dop_data"):
            analysis_params["dop_data"] = self.memory["dop_data"]
        if self.memory.get("cn0_data"):
            analysis_params["cn0_data"] = self.memory["cn0_data"]
        analysis_obs = execute_tool("analyze_positioning_quality", analysis_params)
        self._log_step(
            "Analyzing positioning quality from all extracted data.",
            {"tool": "analyze_positioning_quality", "parameters": analysis_params},
            analysis_obs, time.time() - step_start)
        self._update_memory("analyze_positioning_quality", analysis_obs)

        # Summarise pre-extraction results for the LLM conversation
        ext_summary_parts = []
        for ext in self.memory["extraction_results"]:
            dtype = ext.get("extracted_data", {}).get("diagram_type", "unknown")
            ok = ext.get("success", False)
            ext_summary_parts.append(f"  - {dtype}: {'success' if ok else 'partial (used with warnings)'}")
        analysis_summary = json.dumps(analysis_obs, indent=2, default=str)
        if len(analysis_summary) > 2000:
            analysis_summary = analysis_summary[:2000] + "\n... [truncated]"

        conversation.append({"role": "model", "parts": [json.dumps({
            "thought": "I have extracted data from all available diagrams and analysed positioning quality.",
            "action": {"tool": "analyze_positioning_quality", "parameters": {}}
        })]})
        conversation.append({"role": "user", "parts": [
            f"Extraction and analysis are complete.\n"
            f"Extraction results:\n{''.join(ext_summary_parts)}\n\n"
            f"Analysis results:\n{analysis_summary}\n\n"
            f"Now call generate_diagnostic_report to compile the final report, "
            f"then call TASK_COMPLETE."
        ]})

        # ── Agent Loop (LLM reasons over results, generates report) ────
        while self.iteration < cfg.MAX_AGENT_ITERATIONS:
            self.iteration += 1
            # Rate limit spacing between iterations (cloud APIs need gaps, Ollama doesn't)
            if self.iteration > 1 and cfg.API_PROVIDER != "ollama":
                time.sleep(20)
            step_start = time.time()

            # Get agent's next action from LLM
            try:
                raw = self._call_llm(conversation)
            except Exception as e:
                self._log_step("ERROR", f"LLM call failed: {e}", None, str(e))
                break

            # Parse the agent's response
            parsed = self._parse_agent_response(raw)
            if parsed is None:
                self._log_step(
                    f"Failed to parse agent response",
                    {"tool": "PARSE_ERROR", "parameters": {}},
                    raw,
                    time.time() - step_start
                )
                # Add error feedback and retry
                conversation.append({"role": "model", "parts": [raw]})
                conversation.append({
                    "role": "user",
                    "parts": ["Your response was not valid JSON. Please respond with ONLY a valid JSON "
                              "object following the ReAct format specified in the system prompt."]
                })
                continue

            thought = parsed.get("thought", "")
            action = parsed.get("action", {})
            tool_name = action.get("tool", "")
            parameters = action.get("parameters", {})

            # ── Check for completion ────────────────────────────────────
            if tool_name == "TASK_COMPLETE":
                self._log_step(thought, action, parsed.get("final_answer", "Task complete"),
                               time.time() - step_start)
                break

            # ── Auto-complete if report is done and LLM calls unknown tool
            if tool_name not in ("extract_diagram_data", "analyze_positioning_quality",
                                 "generate_diagnostic_report") and self.memory.get("report"):
                report = self.memory["report"]
                if isinstance(report, dict) and report.get("success"):
                    self._log_step(thought, {"tool": "TASK_COMPLETE", "parameters": {}},
                                   "Auto-completed: report already generated",
                                   time.time() - step_start)
                    break

            # ── Inject memory data into tool parameters ────────────────
            parameters = self._inject_memory_params(tool_name, parameters)

            # ── Execute the tool ────────────────────────────────────────
            observation = execute_tool(tool_name, parameters)
            step_latency = time.time() - step_start

            # Log the step
            self._log_step(thought, action, observation, step_latency)

            # Update memory
            self._update_memory(tool_name, observation)

            # Add to conversation for next iteration
            conversation.append({"role": "model", "parts": [raw]})
            observation_text = json.dumps(observation, indent=2, default=str)
            # Truncate very long observations to stay within context
            if len(observation_text) > 4000:
                observation_text = observation_text[:4000] + "\n... [truncated]"
            conversation.append({
                "role": "user",
                "parts": [f"Observation:\n{observation_text}\n\nContinue with the next step."]
            })

        # ── Build final result ──────────────────────────────────────────
        total_time = time.time() - self.start_time
        return {
            "task": task,
            "trace": self.trace,
            "memory": self.memory,
            "metrics": {
                "total_iterations": self.iteration,
                "total_time_seconds": round(total_time, 2),
                "avg_step_time_seconds": round(total_time / max(self.iteration, 1), 2),
                "tools_called": [s["action"]["tool"] for s in self.trace if isinstance(s.get("action"), dict) and "tool" in s["action"]],
                "success": isinstance(self.memory.get("report"), dict) and self.memory["report"].get("success", False),
            }
        }

    def _parse_agent_response(self, raw: str) -> dict | None:
        """Parse the agent's JSON response, handling common formatting issues."""
        import re
        # Strip markdown fences
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        # Remove any text before the first { or after the last }
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]

        # Fix common local LLM JSON issues: trailing commas, single quotes
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract thought and action manually
            thought_match = re.search(r'"thought"\s*:\s*"([^"]*(?:\\"[^"]*)*)"', text)
            tool_match = re.search(r'"tool"\s*:\s*"([^"]*)"', text)
            if thought_match and tool_match:
                tool_name = tool_match.group(1)
                thought = thought_match.group(1)
                # Try to extract parameters
                params = {}
                params_match = re.search(r'"parameters"\s*:\s*(\{[^}]*\})', text)
                if params_match:
                    try:
                        params = json.loads(params_match.group(1))
                    except json.JSONDecodeError:
                        pass
                return {
                    "thought": thought,
                    "action": {"tool": tool_name, "parameters": params}
                }
            return None

    def _call_llm(self, conversation: list) -> str:
        """Call the configured LLM provider for agent reasoning with retry."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if cfg.API_PROVIDER == "ollama":
                    from openai import OpenAI
                    client = OpenAI(
                        base_url=cfg.OLLAMA_BASE_URL,
                        api_key="ollama",
                    )
                    messages = []
                    for msg in conversation:
                        text = msg["parts"][0] if isinstance(msg["parts"], list) else msg["parts"]
                        role = "user" if msg["role"] == "user" else "assistant"
                        messages.append({"role": role, "content": text})
                    response = client.chat.completions.create(
                        model=cfg.OLLAMA_AGENT_MODEL,
                        messages=messages,
                        max_tokens=4096,
                    )
                    return response.choices[0].message.content.strip()
                elif cfg.API_PROVIDER == "gemini":
                    from google import genai
                    client = genai.Client(api_key=cfg.GEMINI_API_KEY)
                    contents = [
                        msg["parts"][0] if isinstance(msg["parts"], list) else msg["parts"]
                        for msg in conversation
                    ]
                    response = client.models.generate_content(
                        model=cfg.GEMINI_MODEL, contents=contents
                    )
                    return response.text.strip()
                else:
                    from openai import OpenAI
                    client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=cfg.OPENROUTER_API_KEY,
                        timeout=60.0,
                    )
                    messages = []
                    for msg in conversation:
                        text = msg["parts"][0] if isinstance(msg["parts"], list) else msg["parts"]
                        role = "user" if msg["role"] == "user" else "assistant"
                        messages.append({"role": role, "content": text})
                    model = getattr(self, '_current_model', cfg.OPENROUTER_AGENT_MODEL)
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=4096,
                    )
                    return response.choices[0].message.content.strip()
            except Exception as e:
                err_str = str(e)
                # On connection error or 429, try fallback models (cloud only)
                if cfg.API_PROVIDER != "ollama" and ("Connection" in err_str or "429" in err_str) and attempt < max_retries - 1:
                    fallbacks = [
                        cfg.OPENROUTER_AGENT_MODEL_FALLBACK,
                        "meta-llama/llama-3.3-70b-instruct:free",
                    ]
                    self._current_model = fallbacks[attempt % len(fallbacks)]
                    wait = (attempt + 1) * 15
                    time.sleep(wait)
                    continue
                raise

    def _log_step(self, thought, action, observation, latency):
        """Log a single Thought/Action/Observation step."""
        self.trace.append({
            "iteration": self.iteration,
            "thought": thought,
            "action": action,
            "observation": observation,
            "latency_seconds": round(latency, 2) if isinstance(latency, (int, float)) else 0,
        })

    def _inject_memory_params(self, tool_name, parameters):
        """Auto-inject accumulated memory data into tool parameters.

        Small local LLMs struggle to pass large nested data structures as
        tool parameters.  This helper fills in the data the agent has already
        collected so the LLM only needs to name the right tool.
        """
        if tool_name == "analyze_positioning_quality":
            if "satellite_data" not in parameters and self.memory.get("satellite_data"):
                parameters["satellite_data"] = self.memory["satellite_data"]
            if "dop_data" not in parameters and self.memory.get("dop_data"):
                parameters["dop_data"] = self.memory["dop_data"]
            if "cn0_data" not in parameters and self.memory.get("cn0_data"):
                parameters["cn0_data"] = self.memory["cn0_data"]

        elif tool_name == "generate_diagnostic_report":
            if "extraction_results" not in parameters or not parameters["extraction_results"]:
                parameters["extraction_results"] = self.memory.get("extraction_results", [])
            # Auto-run analysis if the LLM skipped analyze_positioning_quality
            if not self.memory.get("analysis_result"):
                from tools import execute_tool as _exec
                analysis_params = {}
                if self.memory.get("satellite_data"):
                    analysis_params["satellite_data"] = self.memory["satellite_data"]
                if self.memory.get("dop_data"):
                    analysis_params["dop_data"] = self.memory["dop_data"]
                if self.memory.get("cn0_data"):
                    analysis_params["cn0_data"] = self.memory["cn0_data"]
                if analysis_params:
                    auto_analysis = _exec("analyze_positioning_quality", analysis_params)
                    self.memory["analysis_result"] = auto_analysis
            if "analysis_results" not in parameters or not parameters["analysis_results"]:
                parameters["analysis_results"] = self.memory.get("analysis_result", {})
            if "task_description" not in parameters:
                parameters["task_description"] = self.memory.get("task", "")

        elif tool_name == "extract_diagram_data":
            # Auto-pick next unprocessed diagram if LLM forgot diagram_type
            if "diagram_type" not in parameters or not parameters["diagram_type"]:
                processed = {
                    r.get("extracted_data", {}).get("diagram_type")
                    for r in self.memory.get("extraction_results", [])
                    if r.get("success")
                }
                for dtype, path in self.memory["available_images"].items():
                    if dtype not in processed:
                        parameters["diagram_type"] = dtype
                        parameters["image_path"] = path
                        break
            # ALWAYS override image_path from available_images when the
            # diagram_type is known — local LLMs often garble Windows paths
            dtype = parameters.get("diagram_type", "")
            if dtype in self.memory.get("available_images", {}):
                parameters["image_path"] = self.memory["available_images"][dtype]

        return parameters

    def _update_memory(self, tool_name, result):
        """Update short-term memory with tool results."""
        if tool_name == "extract_diagram_data":
            self.memory["extraction_results"].append(result)
            # Store extracted data by type for interactive visualizations
            extracted = result.get("extracted_data", {})
            dtype = extracted.get("diagram_type", "")
            if dtype == "sky_plot" and "satellites" in extracted:
                self.memory["satellite_data"] = extracted
            elif dtype == "dop_table" and "epochs" in extracted:
                self.memory["dop_data"] = extracted
            elif dtype == "cn0_chart" and "signals" in extracted:
                self.memory["cn0_data"] = extracted
        elif tool_name == "analyze_positioning_quality":
            self.memory["analysis_result"] = result
        elif tool_name == "generate_diagnostic_report":
            self.memory["report"] = result


def run_diagnostic(task: str = None, images: dict = None) -> dict:
    """
    Convenience function to run the GNSS diagnostic agent.

    If no task/images provided, uses defaults for the sample data.
    """
    import os

    if task is None:
        task = (
            "Perform a comprehensive GNSS positioning quality diagnostic for "
            "station BUAA-REF on 2026-04-11. Analyze the satellite geometry, "
            "signal strength, and DOP values to identify any degraded periods "
            "or risk factors. Provide actionable recommendations for improving "
            "positioning reliability in this environment."
        )

    if images is None:
        images = {
            "sky_plot": os.path.join(cfg.SAMPLES_DIR, "sky_plot.png"),
            "dop_table": os.path.join(cfg.SAMPLES_DIR, "dop_table.png"),
            "cn0_chart": os.path.join(cfg.SAMPLES_DIR, "cn0_chart.png"),
        }

    agent = GNSSDiagnosticAgent()
    return agent.run(task, images)


if __name__ == "__main__":
    # Quick test run
    result = run_diagnostic()
    print(f"\nAgent completed in {result['metrics']['total_iterations']} iterations")
    print(f"Total time: {result['metrics']['total_time_seconds']}s")
    print(f"Success: {result['metrics']['success']}")
    print("\n--- Trace ---")
    for step in result["trace"]:
        print(f"\n[Step {step['iteration']}]")
        print(f"  Thought: {step['thought'][:120]}...")
        if isinstance(step["action"], dict):
            print(f"  Action: {step['action'].get('tool', 'N/A')}")
        print(f"  Latency: {step['latency_seconds']}s")
