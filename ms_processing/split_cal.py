"""Measurement Set splitting utilities."""

from __future__ import annotations

from utils import append_log, get_casa_task


def split_round1_ms(config, input_ms: str | None = None) -> str:
    """Split the calibrated and flagged round-1 Measurement Set."""
    split = get_casa_task("split")
    input_ms = input_ms or config.msvis0
    output_ms = config.msvisr1

    split(vis=input_ms, outputvis=output_ms, datacolumn="corrected")
    append_log(
        config.logfile,
        (
            "Do split the calibrated and flagged measurement set.\n"
            f"Split calibrated round-1 dataset: {output_ms}\n"
            "Split the calibrated and flagged measurement set completed"
        ),
    )
    return output_ms


def split_target_ms(config, input_ms: str | None = None) -> str:
    """Split the final calibrated target field Measurement Set."""
    split = get_casa_task("split")
    input_ms = input_ms or config.msvisr1
    output_ms = config.outputcalvis or config.visname.replace(".ms", ".cal.ms")

    split(
        vis=input_ms,
        outputvis=output_ms,
        datacolumn="corrected",
        field=config.tarfield,
        keepflags=True,
        width=config.specavg,
        timebin=config.timeavg,
    )

    append_log(
        config.logfile,
        (
            "Do split the calibrated dataset.\n"
            f"Split the calibrated dataset for target field: {config.tarfield}\n"
            f"Average the channels by: {config.specavg}\n"
            f"Average the time by: {config.timeavg}\n"
            f"Output calibrated dataset: {output_ms}.\n"
            "Split the calibrated dataset completed"
        ),
    )
    return output_ms
