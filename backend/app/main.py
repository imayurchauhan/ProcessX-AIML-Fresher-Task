from __future__ import annotations

from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / '.env')

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from .evaluator import evaluate_resident_notes, evaluate_resident_notes_async
from .excel_parser import parse_workbook
from .policy_parser import load_policy_document, summarize_policy
from .report_generator import write_issues_to_workbook


app = FastAPI(title='ProcessX Falls Management Compliance Checker', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

ROOT = Path(__file__).resolve().parents[2]
POLICY_FILE = ROOT / 'Falls_Management_Policy_ProcessX.docx'


@app.get('/api/health')
def health() -> dict[str, str]:
    from .llm import groq_available
    return {'status': 'ok', 'engine': 'groq-llm' if groq_available() else 'rule-based'}


@app.get('/api/policy')
def policy() -> dict:
    document = load_policy_document(POLICY_FILE)
    return summarize_policy(document)


@app.post('/api/analyze')
async def analyze(file: UploadFile = File(...)) -> JSONResponse:
    data = await file.read()
    temp_path = ROOT / '._uploaded_input.xlsx'
    temp_path.write_bytes(data)
    residents = parse_workbook(temp_path)
    issues = {}
    engine = 'rule-based'
    for resident in residents:
        resident_issues, used_engine = await evaluate_resident_notes_async(resident.days, resident.resident_name)
        issues[resident.resident_name] = [i.to_dict() for i in resident_issues]
        if used_engine == 'groq-llm':
            engine = 'groq-llm'
    temp_path.unlink(missing_ok=True)
    return JSONResponse({'issues_by_resident': issues, 'engine': engine})


@app.post('/api/generate-output')
async def generate_output(file: UploadFile = File(...)) -> Response:
    data = await file.read()
    temp_input = ROOT / '._input_for_output.xlsx'
    temp_output = ROOT / '._generated_output.xlsx'
    temp_input.write_bytes(data)
    residents = parse_workbook(temp_input)
    issues_by_resident = {}
    for resident in residents:
        resident_issues, _ = await evaluate_resident_notes_async(resident.days, resident.resident_name)
        issues_by_resident[resident.resident_name] = resident_issues
    write_issues_to_workbook(temp_input, temp_output, issues_by_resident)
    content = temp_output.read_bytes()
    temp_input.unlink(missing_ok=True)
    temp_output.unlink(missing_ok=True)
    return Response(
        content=content,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename="ProcessX_Output.xlsx"'},
    )
