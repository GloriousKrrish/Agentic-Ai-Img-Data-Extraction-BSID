# v5.0 Tool Registry & Autonomous Planner Report

## Capability Inventory & Dynamic Selection
The `ToolRegistry` maintains explicit metadata for 14 system capabilities, specifying:
- Determinism flag
- Cost weight & expected latency
- Required permissions

The `AutonomousPlanner` dynamically constructs dependency-tracked execution plans with mandatory critique checkpoints (`s.checkpoint_required=True`).
