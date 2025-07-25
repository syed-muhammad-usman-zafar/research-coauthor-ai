import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("OPENAI_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-flash-latest")


def analyze_knowledge_graph(G):
    # Example: return a list of insights from the knowledge graph
    return [f"Graph has {len(G.nodes)} nodes and {len(G.edges)} edges."]

def generate_full_paper_with_llm(context, papers, knowledge_graph_summary, user_research_context=None):
    """
    Generate the full research paper in a single LLM call, including all major sections, in plain text (not markdown).
    Args:
        context: String with research context (domain, methods, objectives, key concepts, etc.)
        papers: List of dicts with paper metadata for citations
        knowledge_graph_summary: List or string summarizing the knowledge graph
        user_research_context: Optional dict with user research summary
    Returns:
        Dict with 'raw_output' (LLM output string) and 'sections' (dict of section_name: list of paragraphs)
    """
    paper_list = "\n".join([
        f"{p.get('author_names', 'Unknown Author')}, '{p.get('title', 'No Title')}', {p.get('venue', 'Unknown Venue')}, {p.get('year', 'n.d.')}"
        for p in papers
    ])
    kg_summary_str = "\n".join(knowledge_graph_summary) if isinstance(knowledge_graph_summary, list) else str(knowledge_graph_summary)
    user_context_str = ""
    if user_research_context and user_research_context.get('summary'):
        user_context_str = f"\nUser Research: {user_research_context['summary']}"
    prompt = (
        "You are an expert academic writer. Write a full research paper in plain text (not markdown, no # or ## headers). "
        "Start each section with its title (Abstract, Introduction, Literature Review, Methodology, Experiments / Results, Conclusion) on a new line, followed by at least one full paragraph of content. "
        "Do not skip any section. Do not use markdown or # headers. Separate each section with two newlines. Use double newlines between paragraphs. "
        "Use ONLY the following papers for citations (use (Author, Year) style):\n"
        f"{paper_list}\n\n"
        f"Context: {context}{user_context_str}\n"
        f"Knowledge Graph Insights: {kg_summary_str}\n"
        "Do not invent citations, datasets, or references. Ensure every section is present and clearly separated."
    )
    try:
        response = model.generate_content(prompt, generation_config={"max_output_tokens": 1024})
        raw_output = response.text
        # Parse sections by section titles (plain text, not markdown)
        import re
        section_titles = [
            "Abstract", "Introduction", "Literature Review", "Methodology", "Experiments / Results", "Conclusion"
        ]
        pattern = r"(?:^|\n)(%s)\n" % "|".join([re.escape(title) for title in section_titles])
        splits = re.split(pattern, raw_output)
        sections = {}
        for idx, title in enumerate(section_titles):
            # Find the section in splits
            found = False
            for i in range(1, len(splits), 2):
                if splits[i].strip() == title:
                    content = splits[i+1].strip() if i+1 < len(splits) else ""
                    paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 10]
                    if not paragraphs and content:
                        paragraphs = [content]
                    sections[title] = paragraphs
                    found = True
                    break
            if not found:
                sections[title] = ["This section was not generated by the LLM."]
        return {"raw_output": raw_output, "sections": sections}
    except Exception as e:
        print(f"[DEBUG] Gemini generate_full_paper_with_llm failed: {e}")
        section_titles = ["Abstract", "Introduction", "Literature Review", "Methodology", "Experiments / Results", "Conclusion"]
        return {"raw_output": "[Error generating full paper output.]", "sections": {title: ["This section was not generated due to an error."] for title in section_titles}}