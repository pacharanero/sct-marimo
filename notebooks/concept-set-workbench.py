# SPDX-FileCopyrightText: 2026 Marcus Baw and Baw Medical Ltd
# SPDX-License-Identifier: AGPL-3.0-or-later

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    from sct_marimo import AdapterError, QueryRequest, TerminologyAdapter
    from sct_marimo.workbench import compare_concept_sets, inspect_comparison_concept

    return (
        AdapterError,
        QueryRequest,
        TerminologyAdapter,
        compare_concept_sets,
        inspect_comparison_concept,
        mo,
    )


@app.cell
def _(mo):
    mo.md("""
    # SNOMED Solver Workbench

    Compare two supported ECL expressions against one local terminology artefact. Results run only when **Run comparison** is pressed; editing either expression marks the previous result stale.
    """)
    return


@app.cell
def _(mo):
    _db_argument = mo.cli_args().get("db")
    db_path = _db_argument if isinstance(_db_argument, str) and _db_argument else None
    return (db_path,)


@app.cell
def _(mo):
    get_failure, set_failure = mo.state(None)
    get_result, set_result = mo.state(None)
    get_submission, set_submission = mo.state(None)
    return (
        get_failure,
        get_result,
        get_submission,
        set_failure,
        set_result,
        set_submission,
    )


@app.cell
def _(QueryRequest, mo, set_submission):
    candidate_editor = mo.ui.code_editor(
        value="<<73211009",
        language="text",
        label="Candidate ECL expression",
        show_copy_button=False,
        debounce=250,
        min_height=110,
    )
    reference_editor = mo.ui.code_editor(
        value="22298006 OR 46635009",
        language="text",
        label="Reference ECL expression",
        show_copy_button=False,
        debounce=250,
        min_height=110,
    )

    def _submit(sequence):
        next_sequence = sequence + 1
        set_submission(
            (
                next_sequence,
                QueryRequest(
                    candidate_expression=candidate_editor.value,
                    reference_expression=reference_editor.value,
                ),
            )
        )
        return next_sequence

    run_button = mo.ui.button(
        value=0,
        on_click=_submit,
        label="Run comparison",
        keyboard_shortcut="Ctrl-Enter",
    )
    return candidate_editor, reference_editor, run_button


@app.cell
def _(candidate_editor, db_path, mo, reference_editor, run_button):
    _database_status = (
        "A local terminology artefact is selected."
        if db_path is not None
        else "No terminology artefact selected. Launch with -- --db /path/to/sct.db."
    )
    mo.vstack(
        [
            mo.callout(mo.plain_text(_database_status), kind="neutral", title="Artefact"),
            mo.vstack(
                [candidate_editor, reference_editor],
                align="stretch",
                gap=1,
            ),
            run_button,
        ],
        gap=1,
    )
    return


@app.cell
def _(
    AdapterError,
    TerminologyAdapter,
    compare_concept_sets,
    db_path,
    get_submission,
    set_failure,
    set_result,
):
    _submission = get_submission()
    if _submission is not None:
        _, _request = _submission
        if db_path is None:
            set_failure("Select a local terminology artefact before running the comparison.")
        else:
            try:
                with TerminologyAdapter.open(db_path) as _terminology:
                    _comparison = compare_concept_sets(
                        _terminology,
                        _request,
                        display_limit=25,
                    )
            except AdapterError as _error:
                set_failure(str(_error))
            else:
                set_failure(None)
                set_result(_comparison)
    return


@app.cell
def _(
    QueryRequest,
    candidate_editor,
    get_failure,
    get_result,
    mo,
    reference_editor,
):
    _result = get_result()
    _failure = get_failure()
    _draft = QueryRequest(candidate_editor.value, reference_editor.value)
    if _failure is not None:
        _status = mo.callout(
            mo.plain_text(_failure),
            kind="danger",
            title="Comparison failed",
        )
    elif _result is None:
        _status = mo.callout(
            "Run both expressions to create an exact comparison.",
            kind="neutral",
            title="Not run",
        )
    elif _result.is_stale(_draft):
        _status = mo.callout(
            "The expressions have changed. The displayed result is from the last explicit run.",
            kind="warn",
            title="Stale result",
        )
    else:
        _status = mo.callout(
            "The displayed result matches the current expressions.",
            kind="success",
            title="Current result",
        )
    mo.output.replace(_status)
    return


@app.cell
def _(get_result, mo):
    comparison = get_result()
    mo.stop(
        comparison is None,
        mo.callout(
            "No concept-set comparison is available yet.",
            kind="neutral",
            title="Exact set diff",
        ),
    )
    return (comparison,)


@app.cell
def _(comparison, mo):
    _release_label = comparison.release.edition_label
    if comparison.release.release_id:
        _release_label = f"{_release_label} ({comparison.release.release_id})"
    _fingerprint = comparison.release.content_fingerprint or "not recorded"
    mo.vstack(
        [
            mo.md("## Exact set diff"),
            mo.hstack(
                [
                    mo.stat(comparison.added.total_count, label="Added"),
                    mo.stat(comparison.removed.total_count, label="Removed"),
                    mo.stat(comparison.unchanged.total_count, label="Unchanged"),
                ],
                widths="equal",
                wrap=True,
            ),
            mo.plain_text(
                f"Release: {_release_label} | Date: {comparison.release.release_date} | "
                f"Content fingerprint: {_fingerprint}"
            ),
            mo.plain_text(
                "Each category is an exact fully materialized SCTID set. The table below "
                "shows at most 25 concepts per category."
            ),
        ],
        gap=0.75,
    )
    return


@app.cell
def _(comparison, mo):
    _rows = [
        {
            "change": row.membership.value,
            "sctid": row.concept.id,
            "preferred term": row.concept.preferred_term,
            "FSN": row.concept.fsn,
            "active": row.concept.active,
        }
        for row in comparison.rows
    ]
    changes_table = mo.ui.table(
        _rows,
        pagination=True,
        selection="single",
        page_size=10,
        show_column_summaries=False,
        show_data_types=False,
        show_download=False,
        show_search=False,
        label="Displayed concept-set changes",
        wrapped_columns=["preferred term", "FSN"],
    )
    return (changes_table,)


@app.cell
def _(changes_table, comparison, mo):
    _limits = (
        f"Added: showing {comparison.added.returned_count} of {comparison.added.total_count}; "
        f"removed: showing {comparison.removed.returned_count} of {comparison.removed.total_count}; "
        f"unchanged: showing {comparison.unchanged.returned_count} of "
        f"{comparison.unchanged.total_count}."
    )
    mo.vstack(
        [
            mo.plain_text(_limits),
            mo.plain_text(
                "Select one row with its checkbox to open the persistent concept inspector."
            ),
            changes_table,
        ],
        gap=0.5,
    )
    return


@app.cell
def _(
    AdapterError,
    TerminologyAdapter,
    changes_table,
    comparison,
    db_path,
    inspect_comparison_concept,
    mo,
):
    _selected_rows = changes_table.value
    mo.stop(
        not _selected_rows,
        mo.callout(
            "Select a displayed concept to inspect its terminology evidence.",
            kind="neutral",
            title="Concept inspector",
        ),
    )
    _selected_id = str(_selected_rows[0]["sctid"])
    try:
        if db_path is None:
            raise AdapterError("the terminology artefact is no longer selected")
        with TerminologyAdapter.open(db_path) as _terminology:
            inspection = inspect_comparison_concept(
                _terminology,
                comparison,
                _selected_id,
                child_limit=25,
            )
    except AdapterError as _error:
        mo.stop(
            True,
            mo.callout(
                mo.plain_text(str(_error)),
                kind="danger",
                title="Concept inspection failed",
            ),
        )
    return (inspection,)


@app.cell
def _(inspection, mo):
    _concept = inspection.concept
    _parents = [
        {
            "sctid": parent.id,
            "preferred term": parent.preferred_term,
            "FSN": parent.fsn,
            "active": parent.active,
        }
        for parent in inspection.parents
    ]
    _children = [
        {
            "sctid": child.id,
            "preferred term": child.preferred_term,
            "FSN": child.fsn,
            "active": child.active,
        }
        for child in inspection.children.children
    ]
    _attributes = [
        {
            "attribute": attribute.label.replace("_", " "),
            "values": "; ".join(f"{value.fsn} [{value.id}]" for value in attribute.values),
        }
        for attribute in _concept.display_attributes
    ]
    _memberships = [
        {"sctid": membership.id, "preferred term": membership.preferred_term}
        for membership in _concept.member_of
    ]
    _parent_table = mo.ui.table(
        _parents,
        selection=None,
        pagination=False,
        show_column_summaries=False,
        show_data_types=False,
        show_download=False,
        show_search=False,
        label="Direct parents",
    )
    _child_table = mo.ui.table(
        _children,
        selection=None,
        pagination=False,
        show_column_summaries=False,
        show_data_types=False,
        show_download=False,
        show_search=False,
        label="Direct children",
    )
    _attribute_table = mo.ui.table(
        _attributes,
        selection=None,
        pagination=False,
        show_column_summaries=False,
        show_data_types=False,
        show_download=False,
        show_search=False,
        label="Loaded inferred attributes",
    )
    _membership_table = mo.ui.table(
        _memberships,
        selection=None,
        pagination=False,
        show_column_summaries=False,
        show_data_types=False,
        show_download=False,
        show_search=False,
        label="Reference-set memberships",
    )
    mo.vstack(
        [
            mo.md("## Concept inspector"),
            mo.plain_text(f"{_concept.preferred_term} [{_concept.id}]"),
            mo.plain_text(_concept.fsn),
            mo.plain_text(
                f"Active: {_concept.active} | Effective time: {_concept.effective_time} | "
                f"In candidate: {inspection.in_candidate} | In reference: {inspection.in_reference}"
            ),
            mo.plain_text(
                "Hierarchy path is representative only: "
                + " > ".join(_concept.representative_hierarchy_path)
            ),
            mo.md("### Direct parents"),
            _parent_table,
            mo.md("### Direct children"),
            mo.plain_text(
                f"Showing {inspection.children.returned_count} of "
                f"{inspection.children.total_count} direct children with limit "
                f"{inspection.children.limit}. Truncated: {inspection.children.truncated}."
            ),
            _child_table,
            mo.md("### Loaded inferred attributes"),
            mo.plain_text("Attributes are flattened for display and do not preserve role groups."),
            _attribute_table,
            mo.md("### Reference sets and current history evidence"),
            _membership_table,
            mo.plain_text(f"History evidence: {_concept.history_evidence.value}."),
        ],
        gap=0.5,
    )
    return


@app.cell
def _(comparison, mo):
    _invocations = [
        {
            "method": invocation.method,
            "expression": invocation.expression,
            "sct-py version": invocation.sct_py_version,
            "content fingerprint": invocation.content_fingerprint or "not recorded",
        }
        for invocation in comparison.invocations
    ]
    _invocation_table = mo.ui.table(
        _invocations,
        selection=None,
        pagination=False,
        show_column_summaries=False,
        show_data_types=False,
        show_download=False,
        show_search=False,
        label="SDK invocations",
        wrapped_columns=["expression", "content fingerprint"],
    )
    mo.accordion(
        {
            "Reproducibility": mo.vstack(
                [
                    mo.plain_text(
                        f"Candidate result SHA-256: {comparison.candidate.result_sha256}"
                    ),
                    mo.plain_text(
                        f"Reference result SHA-256: {comparison.reference.result_sha256}"
                    ),
                    _invocation_table,
                ]
            )
        }
    )
    return


if __name__ == "__main__":
    app.run()
