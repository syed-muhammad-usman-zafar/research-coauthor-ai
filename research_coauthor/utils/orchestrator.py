from typing import List, Dict, Any
from .citation_agent import calculate_citation_plan, assign_papers_to_sections
from .writing_agent import generate_full_paper_with_llm, analyze_knowledge_graph
from .knowledge_graph import build_knowledge_graph

def generate_full_paper(prompt: str, llm_extracted: Dict[str, Any], 
                       summaries: List[Dict], user_research_context: dict = None) -> Dict[str, Any]:
    """
    Generate a complete academic paper with all sections using neuro-symbolic approach (single LLM call).
    """
    # Extract research elements
    domain = llm_extracted.get('domain', 'General Research')
    keywords = llm_extracted.get('key concepts') or llm_extracted.get('key_concepts', [])
    method = llm_extracted.get('research methods', ['analysis'])[0] if llm_extracted.get('research methods') else 'analysis'
    objective = llm_extracted.get('objectives', ['investigate'])[0] if llm_extracted.get('objectives') else 'investigate'
    # Extract LLM-derived method type and objective scope
    method_type = llm_extracted.get('method_type', method)
    objective_scope = llm_extracted.get('objective_scope', objective)
    # Ensure keywords is a list
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(',') if k.strip()]
    elif not isinstance(keywords, list):
        keywords = list(keywords)
    # Build context string, include user research if present
    context = f"Domain: {domain}\nMethods: {method}\nObjectives: {objective}\nKey Concepts: {', '.join(keywords)}"
    if user_research_context:
        user_summary = user_research_context.get('summary', '')
        context += f"\nUser Research: {user_summary}"
    # Build knowledge graph and summarize
    print("[DEBUG] Building knowledge graph for neuro-symbolic paper generation...")
    knowledge_graph = build_knowledge_graph(
        domain, keywords, method, objective, summaries, context
    )
    kg_summary = analyze_knowledge_graph(knowledge_graph)
    # Generate the full paper in a single LLM call
    try:
        llm_result = generate_full_paper_with_llm(context, summaries, kg_summary, user_research_context)
        # Build References section
        references = []
        for idx, paper in enumerate(summaries):
            venue = paper.get('venue', '')
            venue_clean = venue.strip() if venue else ""
            is_unknown_venue = (venue_clean.lower() in ['unknown venue', 'unknown', 'n/a', ''] or 
                               'unknown' in venue_clean.lower() and 'venue' in venue_clean.lower())
            venue_part = f", {venue_clean}" if venue_clean and not is_unknown_venue else ""
            year = paper.get('year', 'n.d.')
            year_part = f", {year}" if year and year != 'n.d.' else ""
            ref = f"[{idx+1}] {paper['author_names']}, \"{paper['title']}\"{venue_part}{year_part}"
            references.append(ref)
        references_section = "References\n" + "\n".join(references)
        return {
            "title": f"Research on {', '.join(keywords[:3])}",
            "sections": llm_result.get('sections', {}),
            "raw_output": llm_result.get('raw_output', ''),
            "context": context,
            "knowledge_graph": knowledge_graph,
            "references": references_section,
            "papers_found": len(summaries),
            "total_papers_needed": 0,  # or calculate if needed
            "section_assignments": {},  # or fill if needed
        }
    except Exception as e:
        print(f"[DEBUG] generate_full_paper failed: {e}")
        return {
            "title": "Error",
            "sections": {},
            "raw_output": "[Error generating paper.]",
            "context": context,
            "knowledge_graph": knowledge_graph,
            "references": references_section,
            "papers_found": 0,
            "total_papers_needed": 0,
            "section_assignments": {},
        } 