# Claude Code push instructions

Use these steps to apply this package to the target repository.

```bash
git clone https://github.com/wielgosz/PRISMA_S_Lit_Report.git
cd PRISMA_S_Lit_Report

# Copy this package's protocols/ and desktop_runner/ folders into repo root.
# Then inspect changes:
git status

# Optional: run lightweight checks where Python dependencies are available.
python -m py_compile desktop_runner/Supply_Chain_Data_Review_Runner_v2_2_alpha/app.py
python -m py_compile desktop_runner/Supply_Chain_Data_Review_Runner_v2_2_alpha/protocol_engine/run_protocol.py

# Commit
git add protocols/supply_chain_data_review_protocol_v2_1 desktop_runner/Supply_Chain_Data_Review_Runner_v2_2_alpha README.md
git commit -m "Add Supply Chain Data Review Protocol v2.1 and Desktop Runner v2.2-alpha"

git push origin main
```

Recommended follow-up tag:

```bash
git tag supply-chain-data-review-protocol-v2.1-desktop-runner-v2.2-alpha
git push origin supply-chain-data-review-protocol-v2.1-desktop-runner-v2.2-alpha
```

If the repository already has a top-level README that should not be overwritten,
merge the section titled **Desktop Runner v2.2-alpha availability** into the
existing README instead of replacing it.
