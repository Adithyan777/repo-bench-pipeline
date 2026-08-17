"""Pipeline 1: hygiene (detect, pin, dockerfile/compose, build, baseline).

Orchestrated by ``runner.run_hygiene``; each step is a small resumable module.
"""
