from sentence_transformers import SentenceTransformer, util
from utils import get_fonts_and_sizes, solve
import json
from datetime import datetime

model = SentenceTransformer('./model/all-MiniLM-L6-v2')

with open('./input/challenge1b_input.json', 'r') as file:
    data = json.load(file)

# Extract filenames
filenames = [doc['filename'] for doc in data['documents']]

# Extract role
user_persona = data['persona']['role']

# Extract task
query = data['job_to_be_done']['task']

# Function to compute similarity
def is_probable_solution(query, solution):
    # Encode both sentences
    query_emb = model.encode(query, convert_to_tensor=True)
    solution_emb = model.encode(solution, convert_to_tensor=True)

    # Compute cosine similarity
    similarity = util.pytorch_cos_sim(query_emb, solution_emb).item()
    return similarity

collection = []
for pdf_file in filenames:
    pdf_path = "./pdf/"+pdf_file
    threshold = get_fonts_and_sizes(pdf_path)
    results, global_threshold, most_common_font_size, header_lines_greater_than_threshold = solve(pdf_path, threshold)


    font_sizes = [r['font_size'] for r in results]

    # print(f"Global Most Frequent Line GAP: {global_threshold}")
    # print(f"Most Occurred Font Size: {most_common_font_size}")
    # print("-" * 60)

    # Step 1: Collect lines to be printed
    printed_keys = set()
    candidates = []

    # Header lines
    for r in header_lines_greater_than_threshold:
        key = (r['page'], r['line-no'])
        if key in printed_keys:
            continue
        printed_keys.add(key)
        candidates.append({
            "page": r['page'],
            "line-no": r['line-no'],
            "text": r['text'],
            "font_size": r['font_size'],
            "alignment": None,
            "font_style": None,
            "source": "header"
        })

    # Styled & lonely or left-shifted lines
    for i, r in enumerate(results):
        key = (r['page'], r['line-no'])
        if key in printed_keys:
            continue

        if r['alignment'] == "unknown":
            continue

        is_styled = r['font-style'] in {"bold", "bold-italic"}
        is_large_enough = (round(r['font_size'])+1 >= most_common_font_size)
        is_lonely = (r['above_dist'] is None) or (round(r['above_dist']) > global_threshold)

        left_condition = False
        if i + 1 < len(results):
            left_condition = round(r['left_distance']) > round(results[i + 1]['left_distance'])

        if is_styled and is_large_enough and (is_lonely or left_condition):
            printed_keys.add(key)
            candidates.append({
                "page": r['page'],
                "line-no": r['line-no'],
                "text": r['text'],
                "font_size": r['font_size'],
                "alignment": r['alignment'],
                "font_style": r['font-style'],
                "source": "styled"
            })

    # Step 2: Sort candidates by (page, line-no)
    candidates.sort(key=lambda x: (x['page'], x['line-no']))

    # Step 3: Merge adjacent lines only if criteria match
    merged = []
    i = 0
    while i < len(candidates):
        current = candidates[i]
        merged_text = current['text']
        current_font_size = current['font_size']
        current_alignment = current.get('alignment')
        current_font_style = current.get('font_style')
        current_page = current['page']
        last_line_no = current['line-no']

        j = i + 1
        while j < len(candidates):
            next_line = candidates[j]
            same_page = next_line['page'] == current_page
            consecutive = next_line['line-no'] == last_line_no + 1
            same_style = next_line.get('font_style') == current_font_style
            same_align = next_line.get('alignment') == current_alignment
            same_font_size = next_line['font_size'] == current_font_size

            if same_page and consecutive and same_style and same_align and same_font_size:
                merged_text += " " + next_line['text']
                last_line_no = next_line['line-no']
                j += 1
            else:
                break

        merged.append({
            "page": current_page,
            "line-no": last_line_no,
            "text": merged_text.strip(),
            "font_size": current_font_size,
            "alignment": current_alignment,
            "font_style": current_font_style
        })
        i = j

    # Step 4: Print merged results
    unique_sizes = sorted({r['font_size'] for r in merged}, reverse=True)
    size_to_level = {size: f"H{idx + 1}" for idx, size in enumerate(unique_sizes)}

    # Separate page 1 and page >=2 headers
    page1_items = [r for r in merged if r["page"] == 1]
    other_pages = [r for r in merged if r["page"] > 1]

    # Get the largest font size item on page 1
    page1_h1 = None
    if page1_items:
        page1_h1 = max(page1_items, key=lambda x: x["font_size"])

    # Get font sizes from pages >= 2 and sort descending
    other_sizes = sorted({r["font_size"] for r in other_pages}, reverse=True)
    size_to_level = {size: f"H{idx + 1}" for idx, size in enumerate(other_sizes)}

    # Print result in required format
    first = True

    # Print only the page 1 H1
    if page1_h1:
        text_clean = page1_h1['text'].replace('\n', ' ').strip()
        r1 = is_probable_solution(user_persona, text_clean)
        r2 = is_probable_solution(query, text_clean)
        score = r1 * 0.7 + r2 * 0.3
        collection.append({
            "score": score,
            "text": text_clean,
            "pdf": pdf_file,
            "page": page1_h1['page']
        })

    # For other_pages
    for r in other_pages:
        text_clean = r['text'].replace('\n', ' ').strip()
        r1 = is_probable_solution(user_persona, text_clean)
        r2 = is_probable_solution(query, text_clean)
        score = r1 * 0.5 + r2 * 0.5
        collection.append({
            "score": score,
            "text": text_clean,
            "pdf": pdf_file,
            "page": r['page']
        })

collection = sorted(collection, key=lambda x: x["score"], reverse=True)

# Get the largest score
largest_score = collection[0]["score"] if collection else 1  # Avoid divide by zero

# Normalize all scores
#top 5
ct = 0
extracted_sections = []
for item in collection:
    ct = ct+1
    if(ct>5): continue
    x = item["score"] / largest_score
    if(x>=0.5):
        extracted_sections.append({
            "document": item["pdf"],
            "section_title": item["text"],
            "importance_rank": ct,
            "page_number": item["page"]
        })

output = {
    "metadata": {
        "input_documents":list({sec["document"] for sec in extracted_sections}),
        "persona": user_persona,
        "job_to_be_done": query,
        "processing_timestamp": datetime.now().isoformat()
    },
    "extracted_sections": extracted_sections
}

print(json.dumps(output, indent=4))
