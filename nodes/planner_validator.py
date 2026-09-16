from schemas.planner_schema import Step, Tool
# ============================================================
# TOOLS THAT PRODUCE INFORMATION
# ============================================================
RETRIEVAL_TOOLS = {
    Tool.SEARCH,
    Tool.RAG,
}
# ============================================================
# TOOLS THAT CAN DIRECTLY ANSWER
# ============================================================
DIRECT_TOOLS = {
    Tool.CALCULATOR,
    Tool.WEATHER,
    Tool.TRANSLATOR,
    Tool.MAPS,
}
# ============================================================
# CREATE NON-FINAL COPY OF A STEP
# ============================================================
def make_non_final_step(step: Step) -> Step:
    """
    Create a copy of a step that is guaranteed
    not to be the final step.
    """
    return Step(
        tool=step.tool,
        tool_input=step.tool_input,
        output_key=step.output_key,
        depends_on=step.depends_on,
        is_final=False
    )
# ============================================================
# CREATE FINAL SUMMARIZER
# ============================================================
def create_summarizer_step(input_keys: list[str]) -> Step:
    return Step(
        tool=Tool.SUMMARIZER,
        tool_input={
            "input_keys": input_keys
        },
        output_key="final_answer",
        depends_on=input_keys,
        is_final=True
    )
# ============================================================
# VALIDATE AND REPAIR PLAN
# ============================================================
def validate_plan(steps: list[Step]) -> list[Step]:
    if not steps:
        raise ValueError("Planner returned an empty plan.")
    # --------------------------------------------------------
    # Remove duplicate output keys
    # --------------------------------------------------------
    seen_output_keys = set()
    unique_steps = []
    for step in steps:
        if step.output_key in seen_output_keys:
            continue
        seen_output_keys.add(step.output_key)
        unique_steps.append(step)
    steps = unique_steps
    # --------------------------------------------------------
    # Separate summarizer from other tools
    # --------------------------------------------------------
    non_summarizer_steps = [
        step
        for step in steps
        if step.tool != Tool.SUMMARIZER
    ]
    # --------------------------------------------------------
    # Find retrieval steps
    # --------------------------------------------------------
    retrieval_steps = [
        step
        for step in non_summarizer_steps
        if step.tool in RETRIEVAL_TOOLS
    ]
    # --------------------------------------------------------
    # Output keys produced by actual tools
    # --------------------------------------------------------
    output_keys = [
        step.output_key
        for step in non_summarizer_steps
    ]
    # ========================================================
    # CASE 1:
    # Retrieval tool exists
    #
    # SEARCH / RAG must be followed by summarizer.
    # ========================================================
    if retrieval_steps:
        corrected_steps = [
            make_non_final_step(step)
            for step in non_summarizer_steps
        ]
        corrected_steps.append(
            create_summarizer_step(output_keys)
        )
        return corrected_steps
    # ========================================================
    # CASE 2:
    # Multiple direct tools
    #
    # Example:
    # Calculator + Weather + Translator
    #
    # All direct tools execute first.
    # Summarizer combines their outputs.
    # ========================================================
    if len(non_summarizer_steps) > 1:
        corrected_steps = [
            make_non_final_step(step)
            for step in non_summarizer_steps
        ]
        corrected_steps.append(
            create_summarizer_step(output_keys)
        )
        return corrected_steps
    # ========================================================
    # CASE 3:
    # Exactly one direct tool
    #
    # Example:
    # Calculator only
    #
    # Calculator can be the final step.
    # ========================================================
    if len(non_summarizer_steps) == 1:
        step = non_summarizer_steps[0]
        return [
            Step(
                tool=step.tool,
                tool_input=step.tool_input,
                output_key=step.output_key,
                depends_on=step.depends_on,
                is_final=True
            )
        ]
    # ========================================================
    # SAFETY
    # ========================================================
    raise ValueError(
        "Unable to create a valid execution plan."
    )