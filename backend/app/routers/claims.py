import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.claim import ClaimCreate, ClaimOut, ClaimProgressOut, ClaimDocumentOut
from app.schemas.common import APIResponse
from app.services.claim_service import ClaimService

router = APIRouter()


@router.post("", response_model=APIResponse)
async def create_claim(
    data: ClaimCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """申請理賠"""
    svc = ClaimService(db)
    claim = await svc.create_claim(current_user.id, data)
    return APIResponse(data=ClaimOut.model_validate(claim), message=f"理賠已立案，案號：{claim.claim_number}")


@router.get("", response_model=APIResponse)
async def list_claims(
    status: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得理賠列表"""
    svc = ClaimService(db)
    claims = await svc.list_claims(current_user.id, status)
    return APIResponse(data=[ClaimOut.model_validate(c) for c in claims])


@router.get("/{claim_id}", response_model=APIResponse)
async def get_claim(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得理賠詳情"""
    svc = ClaimService(db)
    claim = await svc.get_claim(current_user.id, claim_id)
    return APIResponse(data=ClaimOut.model_validate(claim))


@router.get("/{claim_id}/progress", response_model=APIResponse)
async def get_claim_progress(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得理賠進度"""
    svc = ClaimService(db)
    progress = await svc.get_claim_progress(claim_id)
    return APIResponse(data=[ClaimProgressOut.model_validate(p) for p in progress])


@router.post("/{claim_id}/documents", response_model=APIResponse)
async def upload_document(
    claim_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上傳理賠文件"""
    svc = ClaimService(db)
    doc = await svc.upload_document(claim_id, file, document_type)
    return APIResponse(data=ClaimDocumentOut.model_validate(doc), message="文件已上傳")


@router.get("/{claim_id}/documents", response_model=APIResponse)
async def list_documents(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得理賠文件列表"""
    svc = ClaimService(db)
    claim = await svc.get_claim(current_user.id, claim_id)
    return APIResponse(data=[ClaimDocumentOut.model_validate(d) for d in claim.documents])


@router.get("/{claim_id}/export-csv")
async def export_claim_csv(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """匯出理賠申請 CSV"""
    svc = ClaimService(db)
    claim = await svc.get_claim(current_user.id, claim_id)
    c = ClaimOut.model_validate(claim)
    output = io.StringIO()
    output.write('\ufeff')  # BOM for Excel
    writer = csv.writer(output)
    writer.writerow(["理賠案號", "狀態", "理賠類型", "申請金額", "核准金額", "申請時間", "備註"])
    writer.writerow([c.claim_number, c.status, c.claim_type or '', str(c.claimed_amount or ''),
                     str(c.approved_amount or ''), str(c.submitted_at), c.notes or ''])
    if c.progress_history:
        writer.writerow([])
        writer.writerow(["進度階段", "說明", "時間"])
        for p in c.progress_history:
            writer.writerow([p.stage, p.description or '', str(p.changed_at)])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=claim_{c.claim_number}.csv"},
    )


@router.get("/{claim_id}/export-pdf")
async def export_claim_pdf(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """匯出理賠申請 PDF（列印頁面）"""
    svc = ClaimService(db)
    claim = await svc.get_claim(current_user.id, claim_id)
    c = ClaimOut.model_validate(claim)
    progress_html = ""
    if c.progress_history:
        rows = "".join(f"<tr><td style='padding:6px 8px;border-bottom:1px solid #eee'>{p.stage}</td>"
                       f"<td style='padding:6px 8px;border-bottom:1px solid #eee'>{p.description or ''}</td>"
                       f"<td style='padding:6px 8px;border-bottom:1px solid #eee'>{p.changed_at}</td></tr>"
                       for p in c.progress_history)
        progress_html = f"<h2 style='margin-top:20px;font-size:15px'>進度紀錄</h2><table style='width:100%;border-collapse:collapse;margin-top:8px;font-size:13px'><thead><tr style='background:#f5f5f5'><th style='padding:6px 8px;text-align:left'>階段</th><th style='padding:6px 8px;text-align:left'>說明</th><th style='padding:6px 8px;text-align:left'>時間</th></tr></thead><tbody>{rows}</tbody></table>"
    docs_html = ""
    if c.documents:
        rows = "".join(f"<tr><td style='padding:4px 8px;border-bottom:1px solid #eee'>{d.document_type}</td>"
                       f"<td style='padding:4px 8px;border-bottom:1px solid #eee'>{d.file_name or ''}</td></tr>"
                       for d in c.documents)
        docs_html = f"<h2 style='margin-top:20px;font-size:15px'>相關文件</h2><table style='width:100%;border-collapse:collapse;font-size:13px'><tbody>{rows}</tbody></table>"
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>理賠申請 {c.claim_number}</title>
    <style>body{{font-family:'Microsoft JhengHei',Arial,sans-serif;margin:30px;color:#333}}
    h1{{font-size:20px;color:#1565C0}}table{{width:100%}}th{{text-align:left}}
    .grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin:16px 0}}
    .box{{background:#f8f9fa;border-radius:8px;padding:10px}}.box .l{{font-size:11px;color:#888}}.box .v{{font-size:14px;font-weight:bold;margin-top:2px}}
    .footer{{margin-top:30px;border-top:1px solid #ddd;padding-top:10px;font-size:11px;color:#999}}
    @media print{{body{{margin:15px}}}}</style></head><body>
    <h1>理賠申請書</h1><p style="color:#666;font-size:13px">案號：{c.claim_number}</p>
    <div class="grid">
      <div class="box"><div class="l">狀態</div><div class="v">{c.status}</div></div>
      <div class="box"><div class="l">理賠類型</div><div class="v">{c.claim_type or '--'}</div></div>
      <div class="box"><div class="l">申請金額</div><div class="v">{('$' + str(c.claimed_amount)) if c.claimed_amount else '--'}</div></div>
      <div class="box"><div class="l">核准金額</div><div class="v">{('$' + str(c.approved_amount)) if c.approved_amount else '--'}</div></div>
      <div class="box"><div class="l">申請時間</div><div class="v">{c.submitted_at.strftime('%Y/%m/%d %H:%M') if c.submitted_at else '--'}</div></div>
    </div>
    {f'<p style="margin-top:12px"><b>備註：</b>{c.notes}</p>' if c.notes else ''}
    {progress_html}{docs_html}
    <div class="footer">車險智能服務平台 | 列印日期：{datetime.now().strftime('%Y/%m/%d')}</div>
    <script>window.onload=function(){{window.print();}}</script></body></html>"""
    return HTMLResponse(content=html)
