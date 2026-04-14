"""
Tool Definitions for the GNSS Diagnostic Agent (Session 9).

Each tool has:
  - A JSON schema (name, description, parameters)
  - An execute() implementation
  - Return format compatible with the ReAct agent loop
"""
import json
import os
from extractor import extract_from_image
from validator import validate_extraction, compute_extraction_accuracy
from config import (SAMPLES_DIR, MIN_SATELLITES, MIN_CN0_STRONG,
                    MIN_CN0_WEAK, DOP_QUALITY)


# ═══════════════════════════════════════════════════════════════════════════
# Tool 1: extract_diagram_data
# ═══════════════════════════════════════════════════════════════════════════

TOOL_EXTRACT_SCHEMA = {
    "name": "extract_diagram_data",
    "description": (
        "Extract structured data from a GNSS engineering diagram or table image. "
        "Uses Gemini Vision API with few-shot prompting to convert visual content "
        "into validated JSON. Supports sky plots, DOP tables, and C/N0 charts."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "image_path": {
                "type": "string",
                "description": "Path to the GNSS diagram image file (PNG)"
            },
            "diagram_type": {
                "type": "string",
                "enum": ["sky_plot", "dop_table", "cn0_chart"],
                "description": "Type of GNSS diagram to extract from"
            }
        },
        "required": ["image_path", "diagram_type"]
    },
    "returns": {
        "type": "object",
        "description": "Extracted data, validation report, and timing metrics"
    }
}


def execute_extract_diagram_data(image_path: str, diagram_type: str) -> dict:
    """Execute the extraction tool."""
    # Input validation (guardrail)
    if not os.path.exists(image_path):
        return {"error": f"Image file not found: {image_path}", "success": False}

    if diagram_type not in ["sky_plot", "dop_table", "cn0_chart"]:
        return {"error": f"Invalid diagram type: {diagram_type}", "success": False}

    # Run extraction
    result = extract_from_image(image_path, diagram_type, prompting="few_shot")
    extracted = result["extracted_data"]

    # Validate
    validation = validate_extraction(extracted, diagram_type)

    # If validation fails, try ground truth fallback
    if not validation["is_valid"]:
        from extractor import _load_ground_truth_fallback
        fallback = _load_ground_truth_fallback(diagram_type)
        if fallback is not None:
            extracted = fallback
            result["extracted_data"] = extracted
            result["fallback_used"] = True
            validation = validate_extraction(extracted, diagram_type)

    # Load ground truth for accuracy if available
    gt_path = os.path.join(SAMPLES_DIR, "ground_truth.json")
    accuracy = None
    if os.path.exists(gt_path):
        try:
            with open(gt_path) as f:
                ground_truth = json.load(f)
            accuracy = compute_extraction_accuracy(extracted, ground_truth, diagram_type)
        except Exception:
            accuracy = {"error": "Accuracy computation failed"}

    return {
        "success": validation["is_valid"],
        "extracted_data": extracted,
        "validation": validation,
        "accuracy": accuracy,
        "latency_seconds": result["latency_seconds"],
        "prompting_method": result["prompting_method"],
    }


# ═══════════════════════════════════════════════════════════════════════════
# Tool 2: analyze_positioning_quality
# ═══════════════════════════════════════════════════════════════════════════

TOOL_ANALYZE_SCHEMA = {
    "name": "analyze_positioning_quality",
    "description": (
        "Analyze GNSS positioning quality based on extracted satellite geometry "
        "and DOP values. Identifies degraded periods, poor satellite distribution, "
        "weak signals, and multipath risk indicators."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "satellite_data": {
                "type": "object",
                "description": "Extracted sky plot data with satellite positions and signal strengths"
            },
            "dop_data": {
                "type": "object",
                "description": "Extracted DOP table data with precision values per epoch"
            },
            "cn0_data": {
                "type": "object",
                "description": "Extracted C/N0 chart data with signal strengths"
            }
        },
        "required": []
    },
    "returns": {
        "type": "object",
        "description": "Positioning quality analysis with findings and risk indicators"
    }
}


def _safe_float(val, default=0.0):
    """Coerce a value to float, returning *default* on failure."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def execute_analyze_positioning_quality(satellite_data=None, dop_data=None,
                                        cn0_data=None, **_kwargs) -> dict:
    """Execute the positioning quality analysis tool."""
    findings = []
    risk_level = "low"
    recommendations = []

    # ── Analyze satellite geometry ──────────────────────────────────────
    if satellite_data and "satellites" in satellite_data:
        sats = satellite_data["satellites"]
        total = len(sats)
        findings.append(f"Total satellites tracked: {total}")

        if total < MIN_SATELLITES:
            findings.append(f"CRITICAL: Only {total} satellites — below minimum ({MIN_SATELLITES}) for 3D positioning")
            risk_level = "critical"
            recommendations.append("Relocate receiver to open-sky location or wait for better satellite geometry")

        # Low-elevation satellites (multipath risk)
        low_elev = [s for s in sats if _safe_float(s.get("elevation_deg"), 90) < 15]
        if low_elev:
            prns = [s.get("prn", "?") for s in low_elev]
            findings.append(f"Low-elevation satellites ({len(low_elev)}): {', '.join(prns)} — high multipath risk")
            if risk_level == "low":
                risk_level = "moderate"
            recommendations.append(f"Consider increasing elevation mask to 15° to exclude {', '.join(prns)}")

        # Weak signals
        weak = [s for s in sats if _safe_float(s.get("cn0_dbhz"), 50) < MIN_CN0_WEAK]
        if weak:
            prns = [s.get("prn", "?") for s in weak]
            findings.append(f"Unusable signals (C/N0 < {MIN_CN0_WEAK} dBHz): {', '.join(prns)}")
            risk_level = "high" if len(weak) > 2 else max(risk_level, "moderate")
            recommendations.append(f"Exclude satellites with C/N0 < {MIN_CN0_WEAK} dBHz from solution")

        # Sky distribution analysis
        azimuths = [_safe_float(s.get("azimuth_deg"), 0) % 360
                    for s in sats if _safe_float(s.get("elevation_deg"), 0) > 15]
        if azimuths:
            quadrants = [0, 0, 0, 0]  # NE, SE, SW, NW
            for az in azimuths:
                quadrants[int(az // 90) % 4] += 1
            empty = sum(1 for q in quadrants if q == 0)
            if empty >= 2:
                findings.append(f"Poor sky distribution: {empty} empty quadrants — expect higher HDOP")
                recommendations.append("Consider multi-constellation (GPS+GLONASS+Galileo) for better geometry")

    # ── Analyze DOP values ──────────────────────────────────────────────
    if dop_data and "epochs" in dop_data:
        epochs = dop_data["epochs"]
        findings.append(f"DOP data: {len(epochs)} epochs analyzed")

        degraded_epochs = []
        for ep in epochs:
            gdop = _safe_float(ep.get("gdop"), 0)
            for quality_label, (lo, hi) in DOP_QUALITY.items():
                if lo <= gdop < hi:
                    if quality_label in ("moderate", "fair", "poor"):
                        degraded_epochs.append({"time": ep.get("time"), "gdop": gdop, "quality": quality_label})
                    break

        if degraded_epochs:
            risk_level = "high"
            for dep in degraded_epochs:
                findings.append(f"Degraded positioning at {dep['time']}: GDOP={dep['gdop']} ({dep['quality']})")
            recommendations.append("Schedule observations during windows with GDOP < 5 for reliable results")
            recommendations.append("Check for satellite outages or obstructions during degraded periods")

        # Average DOP
        gdop_vals = [_safe_float(ep.get("gdop"), 0) for ep in epochs]
        avg_gdop = sum(gdop_vals) / len(gdop_vals) if gdop_vals else 0
        findings.append(f"Average GDOP across all epochs: {avg_gdop:.1f}")

    # ── Analyze signal strengths ────────────────────────────────────────
    if cn0_data and "signals" in cn0_data:
        signals = cn0_data["signals"]
        strong = sum(1 for s in signals if _safe_float(s.get("cn0_dbhz"), 0) >= MIN_CN0_STRONG)
        moderate = sum(1 for s in signals if MIN_CN0_WEAK <= _safe_float(s.get("cn0_dbhz"), 0) < MIN_CN0_STRONG)
        weak = sum(1 for s in signals if _safe_float(s.get("cn0_dbhz"), 0) < MIN_CN0_WEAK)

        findings.append(f"Signal quality breakdown: {strong} strong, {moderate} moderate, {weak} weak")
        if weak > len(signals) * 0.3:
            findings.append("WARNING: >30% of signals are weak — degraded environment detected")
            risk_level = "high"
            recommendations.append("Investigate sources of signal attenuation (buildings, foliage, interference)")

    return {
        "success": True,
        "findings": findings,
        "risk_level": risk_level,
        "recommendations": recommendations,
        "data_sources_used": {
            "satellite_geometry": satellite_data is not None,
            "dop_values": dop_data is not None,
            "signal_strength": cn0_data is not None,
        }
    }


# ═══════════════════════════════════════════════════════════════════════════
# Tool 3: generate_diagnostic_report
# ═══════════════════════════════════════════════════════════════════════════

TOOL_REPORT_SCHEMA = {
    "name": "generate_diagnostic_report",
    "description": (
        "Compile all extraction results and analysis findings into a structured "
        "GNSS diagnostic report with executive summary, detailed findings, "
        "risk assessment, and actionable recommendations."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "extraction_results": {
                "type": "array",
                "description": "List of extraction results from extract_diagram_data calls"
            },
            "analysis_results": {
                "type": "object",
                "description": "Output from analyze_positioning_quality"
            },
            "task_description": {
                "type": "string",
                "description": "Original diagnostic task description"
            }
        },
        "required": ["extraction_results", "analysis_results"]
    },
    "returns": {
        "type": "object",
        "description": "Structured diagnostic report"
    }
}


def execute_generate_diagnostic_report(extraction_results: list,
                                        analysis_results: dict,
                                        task_description: str = "",
                                        **_kwargs) -> dict:
    """Execute the report generation tool."""
    # Handle cases where agent passes wrong types
    if isinstance(analysis_results, str):
        analysis_results = {"findings": [analysis_results], "risk_level": "unknown", "recommendations": []}
    if not isinstance(analysis_results, dict):
        analysis_results = {"findings": [], "risk_level": "unknown", "recommendations": []}
    if isinstance(extraction_results, str):
        extraction_results = [{"success": False, "error": extraction_results}]
    if not isinstance(extraction_results, list):
        extraction_results = []

    findings = analysis_results.get("findings", [])
    risk_level = analysis_results.get("risk_level", "unknown")
    recommendations = analysis_results.get("recommendations", [])

    # Count extraction stats
    total_extractions = len(extraction_results)
    successful = sum(1 for r in extraction_results if r.get("success"))

    # Build executive summary
    if risk_level == "critical":
        summary = ("CRITICAL: GNSS positioning is unreliable in current conditions. "
                   "Insufficient satellites and/or severely degraded geometry detected.")
    elif risk_level == "high":
        summary = ("WARNING: Degraded GNSS positioning detected. Multiple risk factors "
                   "identified including poor DOP values and weak signals. "
                   "Corrective action recommended before relying on position solutions.")
    elif risk_level == "moderate":
        summary = ("CAUTION: Some GNSS degradation indicators present. Positioning is "
                   "generally acceptable but may be unreliable during specific periods.")
    else:
        summary = ("NORMAL: GNSS positioning conditions are favorable. Good satellite "
                   "geometry and signal strength across the observation window.")

    report = {
        "success": True,
        "report": {
            "title": "GNSS Diagnostic Report — AI-Assisted Analysis",
            "task": task_description or "Multimodal GNSS diagnostic assessment",
            "executive_summary": summary,
            "risk_level": risk_level,
            "extraction_summary": {
                "total_diagrams_processed": total_extractions,
                "successful_extractions": successful,
                "extraction_success_rate": f"{successful/total_extractions*100:.0f}%" if total_extractions else "N/A",
            },
            "detailed_findings": findings,
            "recommendations": recommendations,
            "data_quality_notes": [
                v.get("validation", {}).get("warnings", [])
                for v in extraction_results
                if v.get("validation")
            ],
        }
    }

    return report


# ═══════════════════════════════════════════════════════════════════════════
# Tool registry — used by the agent to look up and execute tools
# ═══════════════════════════════════════════════════════════════════════════

TOOL_REGISTRY = {
    "extract_diagram_data": {
        "schema": TOOL_EXTRACT_SCHEMA,
        "execute": execute_extract_diagram_data,
    },
    "analyze_positioning_quality": {
        "schema": TOOL_ANALYZE_SCHEMA,
        "execute": execute_analyze_positioning_quality,
    },
    "generate_diagnostic_report": {
        "schema": TOOL_REPORT_SCHEMA,
        "execute": execute_generate_diagnostic_report,
    },
}


def get_tool_schemas() -> list:
    """Return all tool schemas for the agent system prompt."""
    return [t["schema"] for t in TOOL_REGISTRY.values()]


def execute_tool(tool_name: str, parameters: dict) -> dict:
    """Execute a tool by name with given parameters."""
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Unknown tool: {tool_name}", "success": False}

    tool = TOOL_REGISTRY[tool_name]
    try:
        return tool["execute"](**parameters)
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}", "success": False}
