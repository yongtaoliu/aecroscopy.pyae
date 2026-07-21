# LLM Agent

$_{Yongtao}$ $_{Liu,}$
$_{liuy3@ornl.gov,}$ $_{youngtaoliu@gmail.com}$

$_{July}$ $_{2026}$

Large Language Models (LLMs) and agentic AI are transforming how researchers interact with scientific instruments. In AEcroscopy, we integrate LLM-powered agentic AI to allow users to control the microscope and design experiment workflows using natural language — no Python programming experience required.

The ideas in this chapter originated with:

* [Liu, Yongtao, Marti Checa, and Rama K. Vasudevan. "Synergizing Human Expertise and AI Efficiency with Language Model for Microscopy Operation and Automated Experiment Design." Machine Learning: Science and Technology 5.2 (2024).](https://iopscience.iop.org/article/10.1088/2632-2153/ad52e9/meta)

To our knowledge, this was the first exploration of using an LLM for microscopy control.

## What is Agentic AI in AEcroscopy?

An AI agent in AEcroscopy acts as an intelligent interface between the researcher and the microscope. Instead of writing Python scripts manually, users can describe what they want in plain English, and the agent translates those instructions into AEcroscopy commands and executes them automatically.

For example, a user can say:

> *"Perform a raster scan with a 5 µm scan size, then apply a -5 V pulse at the center and image the result."*

The agent interprets the intent, constructs the corresponding AEcroscopy workflow, and runs it — enabling full experiment control through conversation.

## Key Capabilities

- **Natural language microscope control** — Directly operate the AFM (tip movement, scanning, pulsing) by describing actions in plain English.
- **Natural language workflow design** — Compose multi-step automated and autonomous experiment workflows without writing code.
- **Accessibility** — Lowers the barrier to entry for researchers who are not familiar with Python, making automated and autonomous microscopy accessible to a broader scientific community.
- **Interactive experiment guidance** — The agent can suggest next steps, explain parameters, and help users make decisions during an ongoing experiment.

## Why This Matters

Automated and autonomous microscopy workflows have historically required programming expertise to set up and operate. By introducing agentic AI, AEcroscopy enables domain scientists — materials researchers, physicists, chemists — to focus on the science rather than the code, while still benefiting from the full power of automated and AI-driven experimentation.

## How It Works: Under the Hood

Behind the conversation, AEcroscopy runs a four-stage pipeline:

1. **Elicitation** — a planning session has a multi-turn dialogue with an LLM. The LLM either asks a clarifying question, or — once it has enough information — writes the experiment as Python, using the same tool catalog covered in Chapters 2 and 6. This generated script is an implementation detail; a scientist using the pipeline is never expected to read or edit it.
2. **Twin validation** — that generated script is executed against a digital AFM twin, so logic errors are caught before anything touches real hardware.
3. **Human approval** — a validated script is held pending a human reviewer's sign-off. Routine, well-tested requests can be auto-approved; novel ones should always be reviewed.
4. **Scheduling** — an approved script is queued as a job for a specific instrument and executed by the workflow engine, which drives the real Cypher and WaveVI interfaces from Chapter 2.

The LLM itself runs locally via [Ollama](https://ollama.com) — no experiment data or instrument commands leave the lab network.

## Talking to the Microscope Directly

The pipeline above can also be driven conversationally through the Model Context Protocol (MCP) server shipped with AEcroscopy. It exposes the same tool catalog the planner draws from, so any MCP-compatible chat client — Claude Desktop, for instance — can plan, validate, and (after approval) run experiments purely through conversation, without a scientist writing or reading any code.
