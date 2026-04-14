"""
Post-processing & Validation Module (Session 10).

Validates extracted GNSS data against predefined schemas and domain constraints:
  - JSON schema validation (required fields, types)
  - Range checks (elevation 0-90, azimuth 0-360, DOP 0-50, C/N0 0-60)
  - Confidence thresholds
  - Duplicate / conflict detection
"""
from config import VALID_RANGES, CONFIDENCE_THRESHOLD


# ── Schema definitions ──────────────────────────────────────────────────────

SCHEMAS = {
    "sky_plot": {
        "required_keys": ["diagram_type", "satellites", "metadata", "confidence"],
        "satellite_fields": ["prn", "elevation_deg", "azimuth_deg"],
        "optional_fields": ["cn0_dbhz", "signal_quality"],
    },
    "dop_table": {
        "required_keys": ["diagram_type", "epochs", "metadata", "confidence"],
        "epoch_fields": ["time", "gdop", "pdop", "hdop", "vdop", "tdop"],
    },
    "cn0_chart": {
        "required_keys": ["diagram_type", "signals", "metadata", "confidence"],
        "signal_fields": ["prn", "cn0_dbhz"],
    },
}


def validate_extraction(extracted_data: dict, diagram_type: str) -> dict:
    """
    Validate extracted data against schema and domain constraints.

    Returns a validation report with:
      - is_valid: overall pass/fail
      - errors: list of critical errors
      - warnings: list of non-critical issues
      - stats: summary statistics
    """
    errors = []
    warnings = []
    stats = {}

    # If the model returned a list, unwrap the first element
    if isinstance(extracted_data, list):
        if len(extracted_data) > 0 and isinstance(extracted_data[0], dict):
            extracted_data = extracted_data[0]
        else:
            return {
                "is_valid": False,
                "errors": ["Extraction returned an unexpected list format"],
                "warnings": [],
                "stats": {},
            }

    if not isinstance(extracted_data, dict):
        return {
            "is_valid": False,
            "errors": [f"Expected dict, got {type(extracted_data).__name__}"],
            "warnings": [],
            "stats": {},
        }

    if "error" in extracted_data:
        return {
            "is_valid": False,
            "errors": [f"Extraction failed: {extracted_data['error']}"],
            "warnings": [],
            "stats": {},
        }

    schema = SCHEMAS.get(diagram_type)
    if not schema:
        return {
            "is_valid": False,
            "errors": [f"Unknown diagram type: {diagram_type}"],
            "warnings": [],
            "stats": {},
        }

    # ── 1. Required keys check ──────────────────────────────────────────
    # Core data keys (satellites/epochs/signals) are errors; metadata/confidence are warnings
    _soft_keys = {"metadata", "confidence"}
    for key in schema["required_keys"]:
        if key not in extracted_data:
            if key in _soft_keys:
                warnings.append(f"Missing optional key: '{key}' — using defaults")
            else:
                errors.append(f"Missing required key: '{key}'")

    # ── 2. Confidence check ─────────────────────────────────────────────
    raw_confidence = extracted_data.get("confidence", 0)
    # Coerce string confidence labels to numeric values
    if isinstance(raw_confidence, str):
        _conf_map = {"high": 0.95, "medium": 0.70, "moderate": 0.70, "low": 0.40}
        confidence = _conf_map.get(raw_confidence.strip().lower(), 0.50)
    else:
        try:
            confidence = float(raw_confidence)
        except (ValueError, TypeError):
            confidence = 0.50
    stats["confidence"] = confidence
    if confidence < CONFIDENCE_THRESHOLD:
        warnings.append(
            f"Low confidence ({confidence:.2f}) below threshold ({CONFIDENCE_THRESHOLD}). "
            f"Results may need human review."
        )

    # ── 3. Type-specific validation ─────────────────────────────────────
    if diagram_type == "sky_plot":
        errors, warnings, stats = _validate_sky_plot(extracted_data, errors, warnings, stats)
    elif diagram_type == "dop_table":
        errors, warnings, stats = _validate_dop_table(extracted_data, errors, warnings, stats)
    elif diagram_type == "cn0_chart":
        errors, warnings, stats = _validate_cn0_chart(extracted_data, errors, warnings, stats)

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }


def _validate_sky_plot(data, errors, warnings, stats):
    """Validate sky plot extraction."""
    satellites = data.get("satellites", [])
    if not isinstance(satellites, list):
        satellites = [satellites] if isinstance(satellites, dict) else []
    # Coerce non-dict items (strings, numbers) into dicts
    satellites = [s if isinstance(s, dict) else {"prn": str(s)} for s in satellites]
    data["satellites"] = satellites
    stats["num_satellites"] = len(satellites)

    if len(satellites) == 0:
        errors.append("No satellites extracted from sky plot")
        return errors, warnings, stats

    # Auto-fill blank/missing PRNs to avoid false duplicate errors
    for i, sat in enumerate(satellites):
        prn = sat.get("prn", "")
        if not prn or not str(prn).strip():
            sat["prn"] = f"UNK_{i+1}"

    seen_prns = set()
    for i, sat in enumerate(satellites):
        # Check required fields
        for field in SCHEMAS["sky_plot"]["satellite_fields"]:
            if field not in sat:
                errors.append(f"Satellite {i}: missing field '{field}'")

        # Range checks (coerce strings to numbers)
        prn = sat.get("prn", f"unknown_{i}")
        try:
            elev = float(sat["elevation_deg"]) if "elevation_deg" in sat else None
        except (ValueError, TypeError):
            elev = None
        try:
            azim = float(sat["azimuth_deg"]) if "azimuth_deg" in sat else None
        except (ValueError, TypeError):
            azim = None
        try:
            cn0 = float(sat["cn0_dbhz"]) if "cn0_dbhz" in sat else None
        except (ValueError, TypeError):
            cn0 = None

        if elev is not None:
            lo, hi = VALID_RANGES["elevation_deg"]
            if not (lo <= elev <= hi):
                errors.append(f"{prn}: elevation {elev}° out of range [{lo}, {hi}]")

        if azim is not None:
            lo, hi = VALID_RANGES["azimuth_deg"]
            if not (lo <= azim <= hi):
                # Normalize to 0-360 instead of failing
                sat["azimuth_deg"] = azim % 360
                warnings.append(f"{prn}: azimuth {azim}° normalized to {azim % 360}°")

        if cn0 is not None:
            lo, hi = VALID_RANGES["cn0_dbhz"]
            if not (lo <= cn0 <= hi):
                errors.append(f"{prn}: C/N0 {cn0} dBHz out of range [{lo}, {hi}]")

        # Auto-derive cn0_dbhz from signal_quality if missing (llava often omits it)
        quality = sat.get("signal_quality", "")
        if cn0 is None and quality:
            estimated = {"strong": 45.0, "moderate": 35.0, "weak": 22.0}.get(
                quality.lower(), None)
            if estimated is not None:
                sat["cn0_dbhz"] = estimated
                cn0 = estimated
                warnings.append(f"{prn}: cn0_dbhz estimated as {estimated} from quality '{quality}'")
            else:
                warnings.append(f"{prn}: missing cn0_dbhz, could not estimate")

        # Signal quality — auto-derive from cn0 if missing
        if cn0 is not None:
            expected = "strong" if cn0 >= 40 else ("moderate" if cn0 >= 30 else "weak")
            if not quality:
                sat["signal_quality"] = expected
            elif quality.lower() != expected:
                warnings.append(f"{prn}: quality '{quality}' inconsistent with C/N0={cn0} (expected '{expected}')")

        # Duplicate detection
        if prn in seen_prns:
            errors.append(f"Duplicate satellite PRN: {prn}")
        seen_prns.add(prn)

    return errors, warnings, stats


def _validate_dop_table(data, errors, warnings, stats):
    """Validate DOP table extraction."""
    epochs = data.get("epochs", [])
    if not isinstance(epochs, list):
        epochs = [epochs] if isinstance(epochs, dict) else []
    # Coerce non-dict items into dicts
    epochs = [e if isinstance(e, dict) else {"time": str(e)} for e in epochs]
    data["epochs"] = epochs
    stats["num_epochs"] = len(epochs)

    if len(epochs) == 0:
        errors.append("No epochs extracted from DOP table")
        return errors, warnings, stats

    seen_times = set()
    for i, epoch in enumerate(epochs):
        time_str = epoch.get("time", f"epoch_{i}")

        # Check DOP value ranges (coerce strings to numbers)
        for dop_key in ["gdop", "pdop", "hdop", "vdop", "tdop"]:
            val = epoch.get(dop_key)
            if val is not None:
                try:
                    val = float(val)
                    epoch[dop_key] = val
                except (ValueError, TypeError):
                    continue
                lo, hi = VALID_RANGES.get(dop_key, (0, 50))
                if not (lo <= val <= hi):
                    errors.append(f"{time_str}: {dop_key}={val} out of range [{lo}, {hi}]")

        # Check DOP consistency: GDOP >= PDOP >= HDOP and GDOP >= PDOP >= VDOP
        try:
            gdop = float(epoch.get("gdop", 0))
            pdop = float(epoch.get("pdop", 0))
            hdop = float(epoch.get("hdop", 0))
            vdop = float(epoch.get("vdop", 0))
        except (ValueError, TypeError):
            gdop = pdop = hdop = vdop = 0
        if gdop > 0 and pdop > 0:
            if pdop > gdop + 0.5:  # small tolerance for extraction errors
                warnings.append(f"{time_str}: PDOP ({pdop}) > GDOP ({gdop}) — unusual")
            if hdop > pdop + 0.5:
                warnings.append(f"{time_str}: HDOP ({hdop}) > PDOP ({pdop}) — unusual")

        # Duplicate time check
        if time_str in seen_times:
            errors.append(f"Duplicate time epoch: {time_str}")
        seen_times.add(time_str)

    return errors, warnings, stats


def _validate_cn0_chart(data, errors, warnings, stats):
    """Validate C/N0 chart extraction."""
    signals = data.get("signals", [])
    if not isinstance(signals, list):
        signals = [signals] if isinstance(signals, dict) else []
    # Coerce non-dict items (strings, numbers) into dicts
    signals = [s if isinstance(s, dict) else {"prn": str(s)} for s in signals]
    data["signals"] = signals
    stats["num_signals"] = len(signals)

    if len(signals) == 0:
        errors.append("No signals extracted from C/N0 chart")
        return errors, warnings, stats

    seen_prns = set()
    for i, sig in enumerate(signals):
        prn = sig.get("prn", f"unknown_{i}")
        try:
            cn0 = float(sig["cn0_dbhz"]) if "cn0_dbhz" in sig else None
        except (ValueError, TypeError):
            cn0 = None

        if cn0 is not None:
            lo, hi = VALID_RANGES["cn0_dbhz"]
            if not (lo <= cn0 <= hi):
                errors.append(f"{prn}: C/N0 {cn0} dBHz out of range [{lo}, {hi}]")

        # Signal quality — auto-derive from cn0 if missing
        quality = sig.get("signal_quality", "")
        if cn0 is not None:
            expected = "strong" if cn0 >= 40 else ("moderate" if cn0 >= 30 else "weak")
            if not quality:
                sig["signal_quality"] = expected  # auto-fill
            elif quality != expected:
                warnings.append(f"{prn}: quality '{quality}' inconsistent with C/N0={cn0}")

        if prn in seen_prns:
            errors.append(f"Duplicate satellite PRN: {prn}")
        seen_prns.add(prn)

    return errors, warnings, stats


def compute_extraction_accuracy(extracted_data: dict, ground_truth: dict,
                                diagram_type: str) -> dict:
    """
    Compare extracted data against ground truth for evaluation.

    Returns accuracy metrics per field.
    """
    if diagram_type == "sky_plot":
        return _accuracy_sky_plot(extracted_data, ground_truth)
    elif diagram_type == "cn0_chart":
        return _accuracy_cn0(extracted_data, ground_truth)
    elif diagram_type == "dop_table":
        return _accuracy_dop(extracted_data, ground_truth)
    return {"error": f"Unknown diagram type: {diagram_type}"}


def _safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _accuracy_sky_plot(extracted, truth):
    gt_sats = {s.get("prn", f"gt_{i}"): s for i, s in enumerate(truth.get("satellites", []))}
    ex_sats = {s.get("prn", f"ex_{i}"): s for i, s in enumerate(extracted.get("satellites", []))}

    matched = set(gt_sats.keys()) & set(ex_sats.keys())
    missed = set(gt_sats.keys()) - set(ex_sats.keys())
    extra = set(ex_sats.keys()) - set(gt_sats.keys())

    elev_errors, azim_errors, cn0_errors = [], [], []
    for prn in matched:
        gt, ex = gt_sats[prn], ex_sats[prn]
        elev_errors.append(abs(_safe_float(gt.get("elevation")) - _safe_float(ex.get("elevation_deg"))))
        azim_errors.append(abs(_safe_float(gt.get("azimuth")) - _safe_float(ex.get("azimuth_deg"))))
        cn0_errors.append(abs(_safe_float(gt.get("cn0")) - _safe_float(ex.get("cn0_dbhz"))))

    n = len(gt_sats)
    return {
        "detection_rate": len(matched) / n if n else 0,
        "matched": len(matched),
        "missed": list(missed),
        "extra": list(extra),
        "mean_elevation_error_deg": round(sum(elev_errors) / len(elev_errors), 1) if elev_errors else None,
        "mean_azimuth_error_deg": round(sum(azim_errors) / len(azim_errors), 1) if azim_errors else None,
        "mean_cn0_error_dbhz": round(sum(cn0_errors) / len(cn0_errors), 1) if cn0_errors else None,
    }


def _accuracy_cn0(extracted, truth):
    gt_sats = {s.get("prn", f"gt_{i}"): _safe_float(s.get("cn0"))
               for i, s in enumerate(truth.get("satellites", []))}
    ex_sats = {s.get("prn", f"ex_{i}"): _safe_float(s.get("cn0_dbhz"))
               for i, s in enumerate(extracted.get("signals", []))}

    matched = set(gt_sats.keys()) & set(ex_sats.keys())
    cn0_errors = [abs(gt_sats[p] - ex_sats[p]) for p in matched]

    n = len(gt_sats)
    return {
        "detection_rate": len(matched) / n if n else 0,
        "matched": len(matched),
        "missed": list(set(gt_sats.keys()) - matched),
        "extra": list(set(ex_sats.keys()) - set(gt_sats.keys())),
        "mean_cn0_error_dbhz": round(sum(cn0_errors) / len(cn0_errors), 1) if cn0_errors else None,
    }


def _accuracy_dop(extracted, truth):
    gt_epochs = {e.get("time", f"gt_{i}"): e for i, e in enumerate(truth.get("dop_epochs", []))}
    ex_epochs = {e.get("time", f"ex_{i}"): e for i, e in enumerate(extracted.get("epochs", []))}

    matched_times = set(gt_epochs.keys()) & set(ex_epochs.keys())
    dop_errors = {"gdop": [], "pdop": [], "hdop": [], "vdop": [], "tdop": []}

    for t in matched_times:
        for key in dop_errors:
            gt_val = _safe_float(gt_epochs[t].get(key, 0))
            ex_val = _safe_float(ex_epochs[t].get(key, 0))
            dop_errors[key].append(abs(gt_val - ex_val))

    n = len(gt_epochs)
    result = {
        "epoch_detection_rate": len(matched_times) / n if n else 0,
        "matched_epochs": len(matched_times),
        "missed_epochs": list(set(gt_epochs.keys()) - matched_times),
    }
    for key, errs in dop_errors.items():
        result[f"mean_{key}_error"] = round(sum(errs) / len(errs), 2) if errs else None

    return result
