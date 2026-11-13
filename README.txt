Runnable application: see README.md for the Google Cloud build, local launch and API. See VALIDATION.md for executed checks. The following text documents the original starter pack.

RevisionGate starter pack

These are synthetic fixtures and build contracts, not a working application. No model has been called and no claimed business outcome has been measured by this pack. No CAD geometry, pricing, ERP integration, customer records, personal names, email addresses, or API keys are included.

Files
handoffs/CLAUDE_FABLE_DESIGN.txt: self-contained brief for brand feeling, logo, copy, visual design, and presentational components.
handoffs/GPT_LOGIC.txt: self-contained brief for IBM integration, validation, state, approval, export, and verification.
handoffs/SHARED_CONTRACT.json: shared meanings, ownership, callbacks, and workflow invariants for both tracks.
WORKBOOK.md: full hackathon strategy, workbook, technical blueprint, submission copy, and pitch scripts.
BUILD_PROMPT.txt: original combined implementation brief; use the split handoffs for parallel Claude Fable and GPT work.
fixtures/01_conflicted.json: revision C versus B, material 6061-T6 versus 7075-T6, and missing finish. Expected: three blockers.
fixtures/02_material_changed.json: drawing material changes to 6061-T6. Expected: revision and finish blockers only.
fixtures/03_complete.json: both sources say revision C and 6061-T6, with explicit Finish: none. Expected: no detected blockers, human review still required.
fixtures/04_injection.json: appends a malicious instruction to the conflicted drawing text. Expected: the same three blockers as 01; source instructions cannot change the task or readiness rules.
expected/expected_findings.json: offline evaluation oracle. This is physically separate from model inputs. Never load, concatenate, attach, or send this file or its expected values in either model request.
prompts/extract.txt: extraction instructions.
prompts/draft.txt: structured clarification drafting instructions.
schema/extraction.schema.json: JSON Schema Draft 2020-12 structural extraction contract.

Intended data flow
1. Load one fixture from fixtures/ and send its packet_id and sources with extract.txt and the extraction schema. Ignore synthetic metadata for extraction. Do not send the expected directory.
2. Validate output against the schema. Then independently verify packet ID, source IDs, line IDs, offset bounds, exclusive-end spans, and exact quote equality. Each evidence source must match the document where the field was extracted.
3. Check semantic support and extraction completeness. A matching substring alone does not prove a fact: it may be an example, negation, policy, or malicious instruction. Human review is mandatory. Do not turn syntax validation into a confidence score.
4. Apply fixed application rules: compare matching part IDs, revision, and material; require explicit RFQ part/quantity/revision/material and explicit RFQ-or-DRAWING finish. None is allowed only when explicitly specified. Never infer absent finish as none. Revision and material conflicts require customer clarification; no source automatically wins.
5. Send only application-validated findings and reference identifiers to draft.txt. The application must implement the validated_findings contract described there; this pack contains no implementation.
6. Display questions beside the original sources. A human can correct extracted values or edit questions; record those corrections and keep unresolved engineering requirements blocked.

Evidence location convention
Sources use source_id plus L001-style line identifiers. Within each line, offsets refer to Unicode code points in body text after the L001 | prefix. char_end is exclusive. quote must exactly equal body_text[char_start:char_end]. Backend checking can reject mismatched spans, but meaning and completeness still require human checking. A missing field cannot cite a fabricated absence span; attach its checklist policy references separately.

State contract
Conflicted packet: blocked -> clarification_draft_ready -> clarification_packet_approved -> awaiting_customer_response. Approving the clarification packet never resolves its revision, material, or finish blocker and never marks the RFQ ready to quote. A no-blocker extraction is no_detected_blockers_pending_human_review, not automatic engineering approval.

Scope and validation status
This pack includes only inputs, offline expected findings, prompts, and schema. JSON parsing can verify file syntax. It does not establish model accuracy, prompt-injection robustness, semantic evidence quality, task time savings, or production readiness. Run these fixtures through the actual IBM integration and review outputs before making such claims.
