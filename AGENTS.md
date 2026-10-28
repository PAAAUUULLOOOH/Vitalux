# Vitalux repository workflow

- “Vormerken”, “merken”, “nur besprechen” and “noch nicht umsetzen” mean discussion only. Do not edit, push or release until implementation is explicitly requested.
- Establish Stable/Main or Unstable before implementation unless the conversation already establishes it. An existing implementation-and-release instruction remains valid; do not request confirmation again.
- Never promote Unstable to Main without an explicit Stable instruction.
- For each authorized version, review and remove confirmed obsolete code, assets and temporary build outputs. Preserve user data, migration compatibility, required license notices, retained background/color presets and meaningful regression coverage.
- Resource optimizations must preserve rendering quality, design behavior, animation and measurement intervals unless the user explicitly requests a change.
- Review the English README, user guide and DE/EN translations. Document only the features on the current branch. Keep undisclosed Easter eggs out of public guides and release notes.
- App changelogs contain user-facing changes only. Do not list CI, packaging or internal cleanup work. For Stable, compare against the last Stable and write one coherent changelog without presenting existing features as new.
- Run appropriate checks and report the actual changes, tests, released channel/version, limitations and measured cleanup. Never claim an unperformed check or publication.
