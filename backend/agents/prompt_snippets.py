"""Shared prompt fragments injected into specialist and merge calls."""

GROUNDED_DETAIL_INSTRUCTIONS = """
Answer requirements (mandatory):
- Write a detailed, developer-ready answer grounded ONLY in the retrieved chunks above.
- Do not invent APIs, configuration, or code that is not present in the chunks.
- When the documentation includes code snippets, interface definitions, JSON/YAML schemas,
  SQL, HCL, tables, or numbered procedures, include them in your answer using markdown
  code fences and name the source document/section.
- Structure longer answers with clear headings: Summary, Details, Examples (if present in
  docs), Recommendations, and Limitations (only if the docs note gaps).
- Format the entire answer as clean GitHub-flavored Markdown: use ## / ### headings,
  hyphen bullet lists (- item), **bold** for emphasis, and fenced code blocks with a
  language tag (e.g. ```java, ```python, ```sql). Do not use raw asterisk-only bullets
  or unformatted code indented with spaces alone.
- Prefer quoting or paraphrasing the framework text over generic advice.
- If the chunks lack enough detail to answer fully, state what is missing and set
  answer_found=false rather than filling gaps from general knowledge.
""".strip()
