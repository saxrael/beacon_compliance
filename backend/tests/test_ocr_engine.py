from unittest.mock import MagicMock, patch

from backend.src.core.ocr_engine import MultiFormatDocumentExtractor


def test_txt_document_extraction():
    extractor = MultiFormatDocumentExtractor(confidence_threshold=0.90)
    raw_bytes = b"Potter's House Christian Mission UK - Sunday Offering 10th Jan 2026."

    res, flag = extractor.extract_document(
        doc_id="doc_txt_01", filename="offering.txt", content_bytes=raw_bytes
    )

    assert res.doc_id == "doc_txt_01"
    assert "Sunday Offering" in res.extracted_text
    assert res.ocr_confidence_avg == 1.0
    assert res.requires_trustee_ocr_review is False
    assert flag is None


def test_low_confidence_ocr_flagging():
    extractor = MultiFormatDocumentExtractor(confidence_threshold=0.90)
    raw_bytes = b"%PDF-1.4 Scanned blurred image payload"

    res, flag = extractor.extract_document(
        doc_id="doc_scanned_01", filename="receipt_scanned.pdf", content_bytes=raw_bytes
    )

    if res.ocr_confidence_avg < 0.90:
        assert res.requires_trustee_ocr_review is True
        assert flag is not None
        assert flag.doc_id == "doc_scanned_01"


def test_pdf_extraction_success_with_pdfplumber():
    extractor = MultiFormatDocumentExtractor()

    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Page 1 Financial Report Content"
    mock_page.extract_tables.return_value = [[["Date", "Amount"], ["2026-01-01", "100.00"]]]

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]

    mock_pdfplumber = MagicMock()
    mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

    with patch("backend.src.core.ocr_engine.pdfplumber", mock_pdfplumber):
        res, flag = extractor.extract_document("doc_pdf_01", "report.pdf", b"%PDF-mock")

    assert res.file_type == "pdf"
    assert "Page 1 Financial Report Content" in res.extracted_text
    assert len(res.extracted_tables) == 1
    assert res.ocr_confidence_avg == 1.0
    assert flag is None


def test_pdf_extraction_exception_fallback():
    extractor = MultiFormatDocumentExtractor()

    mock_pdfplumber = MagicMock()
    mock_pdfplumber.open.side_effect = RuntimeError("PDF corrupt")

    with patch("backend.src.core.ocr_engine.pdfplumber", mock_pdfplumber):
        res, flag = extractor.extract_document(
            "doc_pdf_err", "corrupt.pdf", b"raw latin1 string text"
        )

    assert res.file_type == "pdf"
    assert "raw latin1 string text" in res.extracted_text
    assert res.ocr_confidence_avg == 0.85
    assert flag is not None


def test_excel_csv_extraction_success():
    extractor = MultiFormatDocumentExtractor()
    csv_bytes = b"Date,Description,Amount\n2026-01-10,Tithes,150.00\n"

    res, _flag = extractor.extract_document("doc_csv_01", "tithes.csv", csv_bytes)

    assert res.file_type == "csv"
    assert "Tithes" in res.extracted_text
    assert len(res.extracted_tables) == 1
    assert res.ocr_confidence_avg == 1.0


def test_excel_xlsx_extraction_mocked():
    extractor = MultiFormatDocumentExtractor()

    mock_df = MagicMock()
    mock_df.to_string.return_value = "Header: Cash Ledger\nRow 1: 500.00"
    mock_df.astype.return_value.values.tolist.return_value = [
        ["Header", "Cash Ledger"],
        ["Row 1", "500.00"],
    ]

    mock_pd = MagicMock()
    mock_pd.read_excel.return_value = mock_df

    with patch("backend.src.core.ocr_engine.pd", mock_pd):
        res, _flag = extractor.extract_document("doc_xlsx_01", "ledger.xlsx", b"xlsx_bytes")

    assert res.file_type == "xlsx"
    assert "Cash Ledger" in res.extracted_text
    assert len(res.extracted_tables) == 1


def test_docx_extraction_success():
    extractor = MultiFormatDocumentExtractor()

    mock_p1 = MagicMock()
    mock_p1.text = "Trustee Meeting Minutes 2026"
    mock_p2 = MagicMock()
    mock_p2.text = "Approved R&P Accounts."

    mock_doc = MagicMock()
    mock_doc.paragraphs = [mock_p1, mock_p2]

    mock_docx = MagicMock()
    mock_docx.Document.return_value = mock_doc

    with patch("backend.src.core.ocr_engine.docx", mock_docx):
        res, _flag = extractor.extract_document("doc_docx_01", "minutes.docx", b"docx_bytes")

    assert res.file_type == "docx"
    assert "Trustee Meeting Minutes 2026" in res.extracted_text
    assert "Approved R&P Accounts." in res.extracted_text


def test_image_ocr_extraction_success():
    extractor = MultiFormatDocumentExtractor()

    mock_img = MagicMock()
    mock_image_mod = MagicMock()
    mock_image_mod.open.return_value = mock_img

    mock_tesseract_mod = MagicMock()
    mock_tesseract_mod.image_to_data.return_value = {"conf": [95, 90, 85]}
    mock_tesseract_mod.image_to_string.return_value = "Scanned Receipt 2026"

    with (
        patch("backend.src.core.ocr_engine.Image", mock_image_mod),
        patch("backend.src.core.ocr_engine.pytesseract", mock_tesseract_mod),
    ):
        res, flag = extractor.extract_document("doc_img_01", "receipt.png", b"png_bytes")

    assert res.file_type == "png"
    assert res.extracted_text == "Scanned Receipt 2026"
    assert res.ocr_confidence_avg == 0.90
    assert flag is None


def test_image_ocr_exception_fallback():
    extractor = MultiFormatDocumentExtractor()

    mock_image_mod = MagicMock()
    mock_image_mod.open.side_effect = RuntimeError("Image unreadable")

    with patch("backend.src.core.ocr_engine.Image", mock_image_mod):
        res, flag = extractor.extract_document("doc_img_err", "bad.jpg", b"bad_image_bytes")

    assert res.file_type == "jpg"
    assert "[IMAGE OCR FAILED — Manual Review Required]" in res.extracted_text
    assert res.ocr_confidence_avg == 0.50
    assert flag is not None


def test_unknown_extension_handling():
    extractor = MultiFormatDocumentExtractor()
    raw_content = b"Unknown format text file content."

    res, _flag = extractor.extract_document("doc_unk_01", "notes.unknown", raw_content)

    assert res.file_type == "unknown"
    assert res.extracted_text == "Unknown format text file content."

    res2, _flag2 = extractor.extract_document(
        "doc_no_ext", "filename_without_extension", raw_content
    )
    assert res2.file_type == "raw"
    assert res2.extracted_text == "Unknown format text file content."
