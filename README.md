# Challenge-1b-Multi-Collection-PDF-Analysis
## Adobe India Hackathon: 

This project extends a PDF heading extraction pipeline by incorporating **semantic similarity scoring** using a pre-trained `SentenceTransformer` model. It intelligently identifies and ranks the most relevant **section titles** from a set of PDFs based on a user's **role** and a **task query**.

---

## Functionality

Given:
- A **user persona** (e.g., "travel planner")
- A **task query** (e.g., "plan a trip to Goa")
- A set of **PDF documents**

This system:
1. Extracts **potential headings** from PDFs using layout features (from Task 1).
2. Uses a **transformer model** to calculate similarity between each heading and the persona/task.
3. Ranks the headings based on relevance and outputs the top sections with normalized importance scores.

---

## Used Methods

- **Sentence Transformers** (`all-MiniLM-L6-v2`) are used to compute **semantic similarity** between:
  - Extracted section titles from PDFs
  - The `persona` and the `task`
- Each heading receives a **composite similarity score**:
  - `score = 0.7 * similarity_to_persona + 0.3 * similarity_to_task` (for main title)
  - `score = 0.5 * similarity_to_persona + 0.5 * similarity_to_task` (for other sections)

