"""Unit tests for Multi-format Document Extraction & OCR Engine (backend/src/core/ocr_engine.py)."""

from backend .src .core .ocr_engine import MultiFormatDocumentExtractor 


def test_txt_document_extraction ():
    extractor =MultiFormatDocumentExtractor (confidence_threshold =0.90 )
    raw_bytes =b"Potter's House Christian Mission UK - Sunday Offering 10th Jan 2026."

    res ,flag =extractor .extract_document (
    doc_id ="doc_txt_01",filename ="offering.txt",content_bytes =raw_bytes 
    )

    assert res .doc_id =="doc_txt_01"
    assert "Sunday Offering"in res .extracted_text 
    assert res .ocr_confidence_avg ==1.0 
    assert res .requires_trustee_ocr_review is False 
    assert flag is None 


def test_low_confidence_ocr_flagging ():
    extractor =MultiFormatDocumentExtractor (confidence_threshold =0.90 )
    raw_bytes =b"%PDF-1.4 Scanned blurred image payload"

    res ,flag =extractor .extract_document (
    doc_id ="doc_scanned_01",filename ="receipt_scanned.pdf",content_bytes =raw_bytes 
    )

    if res .ocr_confidence_avg <0.90 :
        assert res .requires_trustee_ocr_review is True 
        assert flag is not None 
        assert flag .doc_id =="doc_scanned_01"
