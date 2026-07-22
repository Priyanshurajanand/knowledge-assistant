from typing import List, Dict, Any

class RecursiveChunkerService:
    @staticmethod
    def chunk_document(
        pages: List[Dict[str, Any]], 
        chunk_size: int = 750, 
        chunk_overlap: int = 150
    ) -> List[Dict[str, Any]]:
        """
        Chunks a list of parsed pages.
        Returns a list of chunk dicts:
        [{'text': str, 'page_number': int, 'chunk_index': int}]
        """
        chunks = []
        global_chunk_idx = 0
        
        for page in pages:
            text = page["text"]
            page_num = page["page_number"]
            
            # Split text of the current page recursively
            page_splits = RecursiveChunkerService._split_text_recursive(
                text, 
                separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""], 
                max_size=chunk_size, 
                overlap=chunk_overlap
            )
            
            for split_text in page_splits:
                cleaned_text = split_text.strip()
                if cleaned_text:
                    chunks.append({
                        "text": cleaned_text,
                        "page_number": page_num,
                        "chunk_index": global_chunk_idx
                    })
                    global_chunk_idx += 1
                    
        return chunks

    @staticmethod
    def _split_text_recursive(
        text: str, 
        separators: List[str], 
        max_size: int, 
        overlap: int
    ) -> List[str]:
        """Recursively splits text using a hierarchy of separators."""
        final_chunks = []
        
        # Find the correct separator to use
        separator = separators[-1]
        new_separators = []
        for i, sep in enumerate(separators):
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break
                
        # Split text by the selected separator
        if separator != "":
            splits = text.split(separator)
        else:
            splits = list(text)

        # Merge splits into coherent chunks based on target size
        current_doc = []
        current_len = 0
        
        for split in splits:
            # Re-add separator if it wasn't the last empty one
            part = split + (separator if separator != "" else "")
            part_len = len(part)
            
            if part_len > max_size:
                # If a single part is larger than max_size, we must split it recursively
                if current_doc:
                    merged = "".join(current_doc)
                    final_chunks.append(merged)
                    current_doc = []
                    current_len = 0
                
                # Split this oversized part with downstream separators
                if new_separators:
                    recursed_splits = RecursiveChunkerService._split_text_recursive(
                        part, new_separators, max_size, overlap
                    )
                    final_chunks.extend(recursed_splits)
                else:
                    # Fallback: slice directly if we have no separators left
                    for start in range(0, part_len, max_size - overlap):
                        final_chunks.append(part[start : start + max_size])
            else:
                if current_len + part_len > max_size:
                    # Current chunk is full, save it
                    merged = "".join(current_doc)
                    final_chunks.append(merged)
                    
                    # Start new chunk with overlap
                    # We look backwards in current_doc to form the overlap
                    overlap_doc = []
                    overlap_len = 0
                    for prev_part in reversed(current_doc):
                        if overlap_len + len(prev_part) > overlap:
                            break
                        overlap_doc.insert(0, prev_part)
                        overlap_len += len(prev_part)
                        
                    current_doc = overlap_doc + [part]
                    current_len = overlap_len + part_len
                else:
                    current_doc.append(part)
                    current_len += part_len
                    
        # Append remaining text
        if current_doc:
            final_chunks.append("".join(current_doc))
            
        return final_chunks
