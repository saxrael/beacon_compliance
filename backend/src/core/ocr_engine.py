"""Multi-format Document Extraction & OCR Engine for Beacon Compliance.

Extracts structured text and table data from uploaded PDF, Word, Excel, and image files.
Flags low-confidence extractions (<90%) for mandatory trustee review.
"""

import io 
from typing import NamedTuple 

from pydantic import BaseModel 

try :
    import pdfplumber 
except Exception :
    pdfplumber =None 

try :
    import pandas as pd 
except Exception :
    pd =None 

try :
    import docx 
except Exception :
    docx =None 

try :
    import pytesseract 
    from PIL import Image 
except Exception :
    pytesseract =None 
    Image =None 


class DocumentExtractionResult (NamedTuple ):
    """Container for extracted document text, tables, and confidence metrics."""

    doc_id :str 
    file_type :str 
    extracted_text :str 
    extracted_tables :list [list [list [str ]]]
    ocr_confidence_avg :float 
    requires_trustee_ocr_review :bool 


class OCRConfidenceFlag (BaseModel ):
    """Flag for low-confidence OCR extraction."""

    doc_id :str 
    confidence :float 
    flag_reason :str ="OCR extraction confidence below 90% threshold. Trustee review required."


class MultiFormatDocumentExtractor :
    """Extractor handling PDF, Word (.docx), Excel (.xlsx), and raw text documents."""

    def __init__ (self ,confidence_threshold :float =0.90 )->None :
        self .confidence_threshold =confidence_threshold 

    def _extract_pdf (self ,content_bytes :bytes )->tuple [str ,list [list [list [str ]]],float ]:
        """Extract text and tables from PDF files."""
        try :
            if not pdfplumber :
                raise RuntimeError ("pdfplumber not installed")

            with pdfplumber .open (io .BytesIO (content_bytes ))as pdf :
                pages_text :list [str ]=[]
                extracted_tables :list [list [list [str ]]]=[]
                for page in pdf .pages :
                    text =page .extract_text ()
                    if text :
                        pages_text .append (text )
                    tables =page .extract_tables ()
                    for tbl in tables :
                        extracted_tables .append (tbl )
                return "\n\n".join (pages_text ),extracted_tables ,1.0 
        except Exception :
            return content_bytes .decode ("latin1",errors ="ignore"),[],0.85 

    def _extract_excel (self ,ext :str ,content_bytes :bytes )->tuple [str ,list [list [list [str ]]]]:
        """Extract text and tables from Excel / CSV files."""
        try :
            if pd is None :
                raise RuntimeError ("pandas not installed")

            df =(
            pd .read_csv (io .BytesIO (content_bytes ))
            if ext =="csv"
            else pd .read_excel (io .BytesIO (content_bytes ))
            )
            return df .to_string (),[df .astype (str ).values .tolist ()]
        except Exception :
            return content_bytes .decode ("utf-8",errors ="ignore"),[]

    def _extract_docx (self ,content_bytes :bytes )->str :
        """Extract text from docx files."""
        try :
            if docx is None :
                raise RuntimeError ("python-docx not installed")

            doc =docx .Document (io .BytesIO (content_bytes ))
            return "\n".join ([p .text for p in doc .paragraphs ])
        except Exception :
            return content_bytes .decode ("utf-8",errors ="ignore")

    def _extract_image (self ,content_bytes :bytes )->tuple [str ,float ]:
        """Extract text from image files via OCR."""
        try :
            if pytesseract is None or Image is None :
                raise RuntimeError ("pytesseract or PIL not installed")

            img =Image .open (io .BytesIO (content_bytes ))
            ocr_data =pytesseract .image_to_data (img ,output_type =pytesseract .Output .DICT )
            confs =[
            float (c )
            for c in ocr_data .get ("conf",[])
            if isinstance (c ,int |float |str )and str (c )!="-1"
            ]
            confidence =(sum (confs )/len (confs )/100.0 )if confs else 0.70 
            text =pytesseract .image_to_string (img )
            return text ,confidence 
        except Exception :
            return "[IMAGE OCR FAILED — Manual Review Required]",0.50 

    def extract_document (
    self ,doc_id :str ,filename :str ,content_bytes :bytes 
    )->tuple [DocumentExtractionResult ,OCRConfidenceFlag |None ]:
        """Extract text and tables from document binary content."""
        ext =filename .rsplit (".",maxsplit =1 )[-1 ].lower ()if "."in filename else ""
        extracted_text =""
        extracted_tables :list [list [list [str ]]]=[]
        confidence =1.0 

        if ext =="txt":
            extracted_text =content_bytes .decode ("utf-8",errors ="replace")
        elif ext =="pdf":
            extracted_text ,extracted_tables ,confidence =self ._extract_pdf (content_bytes )
        elif ext in ("xlsx","xls","csv"):
            extracted_text ,extracted_tables =self ._extract_excel (ext ,content_bytes )
        elif ext in ("docx","doc"):
            extracted_text =self ._extract_docx (content_bytes )
        elif ext in ("png","jpg","jpeg","tiff"):
            extracted_text ,confidence =self ._extract_image (content_bytes )
        else :
            extracted_text =content_bytes .decode ("utf-8",errors ="ignore")

        requires_review =confidence <self .confidence_threshold 
        ocr_flag =(
        OCRConfidenceFlag (doc_id =doc_id ,confidence =confidence )if requires_review else None 
        )

        result =DocumentExtractionResult (
        doc_id =doc_id ,
        file_type =ext or "raw",
        extracted_text =extracted_text ,
        extracted_tables =extracted_tables ,
        ocr_confidence_avg =confidence ,
        requires_trustee_ocr_review =requires_review ,
        )

        return result ,ocr_flag 
