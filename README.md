## Claims
1. Norms/principles in software engineering (SE) shape how software is written and talked about (style guides, naming conventions, review practices, “professionalism,” etc.).
2. Those norms shape the text/code distribution that ends up in public repos, docs, tickets, forums, and therefore in LLM training corpora.
3. Training an LLM to predict that distribution causes it to learn and reproduce some biased associations (racism/sexism/antisemitism) in measurable ways.

## Statement
If SE norms measurably change the distribution of code/text (compared to a counterfactual world), and if LLM training approximates that distribution, then LLM outputs will reflect those changes — including biased associations — and we can quantify the effect.

### Examples
**A. Standardization + “professionalism” filters**
- Style rules about “clear/standard English,” “professional language,” “no slang,” etc. can suppress dialects and certain community norms.
- “Polite/professional” norms sometimes penalize people who speak more directly (gender/race-linked in many workplaces), affecting who gets accepted/merged and whose text persists.

B. Code review + gatekeeping dynamics
- Review processes decide whose code/comments get merged and whose get rewritten.
- If reviewers systematically rewrite certain authors more, the surviving corpus becomes more homogenous (and potentially more aligned with dominant cultural norms).

C. Naming conventions and legacy vocabularies
- Historical terms (e.g., “master/slave,” “blacklist/whitelist,” etc.) are classic examples of socially loaded vocabulary that can persist through “consistency” principles.
- Even when replaced, older text may remain in archives and documentation.

D. Canon formation (DRY, reuse, “best practices”)
- “Don’t reinvent the wheel” + heavy reuse means a small set of canonical libraries/docs get replicated at scale.
- If those canonical sources contain biased examples, stereotypes, or exclusionary language, reuse amplifies it.

E. Benchmarking culture
- What gets measured gets optimized. If “readability,” “tone,” or “helpfulness” rubrics encode biased norms, LLM alignment (or internal tooling) can inherit them.

## Questions
