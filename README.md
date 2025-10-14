# LabOp-Scheduler



This Python script is designed to automate the complex task of scheduling student lab assistants based on their availability preferences, ensuring equitable workload distribution and maximum coverage.

Features
Customizable Constraints: Easily adjust the number of students required per shift (SLOTS_PER_HOUR) and the maximum hours per student (MAX_HOURS_PER_STUDENT).

Intelligent Prioritization: Uses a multi-phase greedy algorithm to prioritize assignments, guaranteeing high-priority slots are filled first.

Flexible Data Handling: Automatically cleans and maps messy, indexed CSV headers (e.g., 9 AM - 10 AM2) to clean internal slot names (e.g., Wednesday 9 AM - 10 AM).

Dual Output Formats: Produces the final schedule in two formats: a concise Calendar CSV
