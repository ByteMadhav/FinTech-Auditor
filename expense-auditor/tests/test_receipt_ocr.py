import pytest
from unittest.mock import patch
from PIL import Image
import numpy as np
from tasks.celery_worker import extract_receipt_data


def create_test_image(tmp_path):
    img_array = np.ones((100, 400, 3), dtype=np.uint8) * 255
    img = Image.fromarray(img_array)
    img_path = str(tmp_path / "test_receipt.png")
    img.save(img_path)
    return img_path


def test_extract_receipt_data_reads_ocr(tmp_path):
    img_path = create_test_image(tmp_path)
    mock_ocr_text = "Advanced Python & SQL Certification Course Tuition –\n$1,200"

    with patch("tasks.celery_worker.pytesseract.image_to_string", return_value=mock_ocr_text):
        result = extract_receipt_data(img_path)

    assert result["raw_text"] == mock_ocr_text.strip()
    assert result["ocr_text"] == mock_ocr_text.strip()
    assert result["merchant"] == ""
    assert result["amount"] == 0


def test_normalize_extracts_merchant_and_amount():
    from app.ai_agent import ComplianceAgent
    import asyncio

    agent = ComplianceAgent.__new__(ComplianceAgent)

    state = {
        "reasoning_steps": [],
        "receipt_data": {
            "raw_text": "Advanced Python & SQL Certification Course Tuition – $1,200",
            "ocr_text": "Advanced Python & SQL Certification Course Tuition – $1,200",
            "merchant": "",
            "amount": 0,
            "date": "Unknown",
            "category": "Other"
        }
    }

    result = asyncio.run(agent._step_extract_normalize(state))

    assert result["normalized_data"]["amount"] == 1200.0
    assert "Advanced Python" in result["normalized_data"]["merchant"]
    assert "SQL Certification" in result["normalized_data"]["merchant"]
    assert "None" not in result["normalized_data"]["merchant"]
    assert "Unknown" not in result["normalized_data"]["merchant"]


def test_normalize_fallback_when_no_merchant():
    from app.ai_agent import ComplianceAgent
    import asyncio

    agent = ComplianceAgent.__new__(ComplianceAgent)

    state = {
        "reasoning_steps": [],
        "receipt_data": {
            "raw_text": "$500",
            "ocr_text": "$500",
            "merchant": "",
            "amount": 0,
            "date": "Unknown",
            "category": "Other"
        }
    }

    result = asyncio.run(agent._step_extract_normalize(state))

    assert result["normalized_data"]["amount"] == 500.0
    assert result["normalized_data"]["merchant"] != "None"
    assert result["normalized_data"]["merchant"] != ""


def test_extract_receipt_data_structure(tmp_path):
    img_path = create_test_image(tmp_path)

    with patch("tasks.celery_worker.pytesseract.image_to_string", return_value="Course Fee $1,200"):
        result = extract_receipt_data(img_path)

    assert "raw_text" in result
    assert "ocr_text" in result
    assert "merchant" in result
    assert "amount" in result
    assert "date" in result
    assert "category" in result