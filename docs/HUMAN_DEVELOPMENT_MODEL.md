# Human Development Model

## 1. Claim boundary

HUMAN VECTOR evaluates observable changes in a participant's work process during a bounded application session or comparable repeated sessions. It does **not** diagnose cognition, measure intelligence, prove learning, or support universal claims about human development. AI supplies pressure and contrast; any demonstrated human development is evidenced by the human's own actions.

The product MUST keep three layers separate:

1. **Observed application events** — timestamped actions and artifacts.
2. **Calculated indicators** — reproducible transformations of those events.
3. **Interpretive claims** — cautious, contextual statements with limitations.

No interpretive statement may be stored as though it were a raw observation.

## 2. Observation design

An assessment window identifies a project, participant pseudonym or local actor identifier, start/end events, protocol stages included, and whether the window is a single-cycle observation or a comparison with a declared baseline. Clock-derived measures MUST state whether AI wait time, inactive time, and interruptions are excluded.

Useful observed events include:

- first opening of V1 and first recorded human weak-point critique;
- human contributions created before and after critic exposure;
- explicit human new ideas and their relation to existing artifacts;
- acceptance, partial acceptance, rejection, reversal, and justification;
- contradictions detected and linked items;
- verification actions, evidence inspected, and outcomes;
- changes to direction and the human's stated reason;
- provenance-inspection actions;
- final selection and unresolved-risk acknowledgment.

Silence, cursor movement, or time on page MUST NOT be treated as cognitive evidence without an explicit, justified measurement rule.

## 3. Indicator catalog

| Indicator | Reproducible calculation | Guardrail |
|---|---|---|
| Time to identify a weak point | active elapsed time from V1 first viewed to first qualifying `HUMAN_CRITIQUE` | Report context and excluded idle time; faster is not always better |
| Independent human ideas | count of distinct `HUMAN_NEW_IDEA` records whose creation precedes any matching transferred/retrieved source | “Independent” is provenance-relative, not proof of mental origin |
| Justification completeness | proportion of required decisions with a non-empty reason meeting declared fields: claim, basis, consequence | Do not score eloquence or personality |
| Incorrect-AI rejection | count/rate of seeded or verified-invalid AI items rejected by the human | Requires a defensible ground-truth or verification record |
| Contradiction detection | verified contradictions first identified by the human / contradictions in the declared evaluation set | Do not claim completeness outside that set |
| Verification behavior | number and diversity of explicit verification actions before final decision | More actions do not automatically mean better quality |
| Direction precision | change in satisfied rubric fields for scope, constraints, criteria, and exclusions | Rubric must be fixed before comparison |
| Passive acceptance | accepted AI items without recorded review/justification divided by reviewed AI items | UI defaults must not manufacture acceptance |
| Origin discrimination | correct origin classifications in a blinded, predefined check | Optional; never infer from normal navigation |
| Final selection quality | satisfied predefined solution criteria, with verification evidence, for the human-selected final | Keep separate from process indicators |

Indicators SHOULD be shown as values with numerator, denominator, event links, calculation version, and uncertainty/limitations. Composite scores are discouraged for the MVP; if later introduced, their weights and value judgments MUST be visible and versioned.

## 4. Qualifying human new ideas

A `HUMAN_NEW_IDEA` is a human-authored proposition deliberately marked as new and recorded separately. The system checks only provenance novelty: whether substantively matching content was already visible to or transferred to the human in recorded application state. It MUST NOT claim access to the person's unrecorded knowledge or thoughts. Similarity tools may flag possible overlap, but the human can annotate the relationship and the raw evidence remains inspectable.

## 5. Comparison strategy

The fictional demonstration SHOULD use within-run evidence plus a predefined scenario rubric. If comparing cycles, keep task difficulty, available evidence, UI conditions, and timing policy as stable as practical. Report confounds such as familiarity with the scenario or different agent output. One demonstration supports only a statement like: “Within this recorded scenario, the participant performed these additional independent, critical, and verification actions.”

## 6. Interpretation vocabulary

Permitted language includes “observed,” “in this run,” “consistent with,” “the record shows,” and “suggests within the scenario.” Prohibited language without external scientific validation includes “proves cognitive growth,” “makes users smarter,” “diagnoses overreliance,” “educates automatically,” or population-level causal claims.

Example bounded interpretation:

> In this demonstration, the human rejected one verified-invalid critic claim, introduced one provenance-distinct idea, and performed two evidence checks before final selection. These events are consistent with more active evaluation in this run; they do not establish general cognitive improvement.

## 7. Anti-gaming and UX requirements

- The application MUST not award points for rejecting AI indiscriminately.
- Accepted and rejected items are evaluated by reasoning and verification, not by disposition alone.
- Human critique SHOULD occur before critic output is revealed when the demonstration measures independent weak-point detection.
- Required reasons MUST not be prefilled with AI-authored text labeled as human justification.
- The application MUST disclose seeded contradictions or ground truth after the assessment, not while it would invalidate the observation.
- Participants MUST be able to inspect and correct misclassified events.

## 8. Minimum assessment output

The assessment view includes the window and calculation policy, linked observed events, individual indicators, limitations/confounds, solution-quality results, and a clearly separate bounded interpretation. Raw artifacts and provenance remain primary; the summary is never the sole evidence.
