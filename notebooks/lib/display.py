from html import escape
from IPython.display import HTML, Markdown, display
import pandas as pd


def display_dataframe_scrollable(
    df: pd.DataFrame, *, max_height: str = "32rem"
) -> None:
    """HTML table in a scrollable panel (wide/tall grouped score stats)."""
    html = df.to_html(classes=("dataframe",), border=0, escape=True, max_rows=None)
    display(
        HTML(
            f'<div style="max-height:{max_height};overflow:auto;width:100%;'
            'border:1px solid #ddd;padding:0.35rem;background:#fafafa">'
            f"{html}</div>"
        )
    )


def display_all_zero_score_comment_samples(
    df: pd.DataFrame,
    *,
    limit: int = 500,
    preview_chars: int = 600,
) -> None:
    """Scrollable panel of truncated cleaned_text for rows with all-zero scores."""
    from .stats import all_zero_scores_mask

    if "cleaned_text" not in df.columns:
        return
    sub = df.loc[all_zero_scores_mask(df)].copy()
    if sub.empty:
        return
    cap = max(1, min(int(limit), 500))
    sub = sub.head(cap)
    chunks: list[str] = []
    for _, r in sub.iterrows():
        raw = str(r.get("cleaned_text") or "")
        preview = raw[:preview_chars] + ("…" if len(raw) > preview_chars else "")
        chunks.append(
            f"comment_id={r.get('comment_id')}  model={r.get('model_name')}  "
            f"repo={r.get('repo')}\n{preview}\n{'-' * 60}\n"
        )
    body = escape("".join(chunks))
    html = (
        '<div style="max-height:48rem;overflow:auto;border:1px solid #ccc;'
        'padding:0.6rem;background:#f9f9f9;font-family:ui-monospace,monospace">'
        f'<pre style="margin:0;white-space:pre-wrap;font-size:12px;line-height:1.35">{body}</pre>'
        "</div>"
    )
    display(HTML(html))
