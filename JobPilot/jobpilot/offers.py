"""Offer records keep negotiation facts separate from application stages."""
from __future__ import annotations
import json
from datetime import date
from pathlib import Path
from typing import Literal
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field, create_model, field_validator, model_validator
from . import db

SCHEMA = json.loads(Path(__file__).with_name('offer-schema.json').read_text())
GROUPS = {group['key'] for group in SCHEMA['groups']}


class Evidence(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    status: Literal['unknown','verbal','written'] = 'unknown'
    source: str = Field(default='',max_length=3000)
    confirmed_date: str = Field(default='',max_length=10)

    @field_validator('confirmed_date')
    @classmethod
    def valid_date(cls,value):
        return check_date(value)


def check_date(value: str) -> str:
    if value:
        try:
            if date.fromisoformat(value).isoformat() != value:raise ValueError()
        except ValueError:raise ValueError('请填写有效日期（YYYY-MM-DD）。')
    return value


class CustomCriterion(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    name: str = Field(min_length=1,max_length=80)
    value: str = Field(default='',max_length=2000)
    source: str = Field(default='',max_length=1000)


class PayPhase(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    phase_type: Literal['internship','trainee','probation','regular','other'] = 'probation'
    duration_months: float|None = Field(default=None,ge=0,le=36,allow_inf_nan=False)
    pay_method: Literal['unknown','fixed','discount','annual_reference'] = 'unknown'
    monthly_amount: float|None = Field(default=None,ge=0,le=1_000_000_000,allow_inf_nan=False)
    percentage: float|None = Field(default=None,ge=0,le=100,allow_inf_nan=False)
    discount_base_type: Literal['unknown','regular','specified'] = 'unknown'
    discount_base_monthly: float|None = Field(default=None,ge=0,le=1_000_000_000,allow_inf_nan=False)
    annual_amount: float|None = Field(default=None,ge=0,le=1_000_000_000,allow_inf_nan=False)
    annual_low: float|None = Field(default=None,ge=0,le=1_000_000_000,allow_inf_nan=False)
    annual_high: float|None = Field(default=None,ge=0,le=1_000_000_000,allow_inf_nan=False)
    annual_scope: str = Field(default='',max_length=800)
    included_in_first_year: bool = False
    start_date: str = Field(default='',max_length=10)
    end_date: str = Field(default='',max_length=10)
    agreement: str = Field(default='',max_length=800)
    notes: str = Field(default='',max_length=3000)
    evidence: Evidence = Field(default_factory=Evidence)

    @model_validator(mode='after')
    def valid_phase(self):
        check_date(self.start_date);check_date(self.end_date)
        if self.start_date and self.end_date and self.start_date>self.end_date:raise ValueError('待遇阶段的结束日期不能早于开始日期。')
        if self.pay_method == 'annual_reference' and self.annual_low is not None and self.annual_high is not None and self.annual_low > self.annual_high:
            raise ValueError('阶段年收入参考区间的下限不能高于上限。')
        return self


class DetailsBase(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    evidence: dict[str,Evidence] = Field(default_factory=dict)
    custom: list[CustomCriterion] = Field(default_factory=list,max_length=50)
    pay_phases: list[PayPhase] = Field(default_factory=list,max_length=12)

    @model_validator(mode='after')
    def valid_content(self):
        if set(self.evidence)-GROUPS:raise ValueError('未知的确认信息分组。')
        names=[item.name.casefold() for item in self.custom]
        if len(names)!=len(set(names)):raise ValueError('同一 Offer 的自定义维度名称不能重复。')
        for group in SCHEMA['groups']:
            for field in group['fields']:
                value=getattr(self,field['key'])
                if field['kind']=='date':check_date(value)
                if field['kind']=='select' and value not in {option['value'] for option in field['options']}:
                    raise ValueError(field['label']+'请选择有效选项。')
                if field['kind']=='time' and value:
                    try:
                        hours,minutes=value.split(':')
                        if len(value)!=5 or not 0<=int(hours)<=23 or not 0<=int(minutes)<=59:raise ValueError()
                    except (ValueError,TypeError):raise ValueError('请填写有效时间（HH:MM）。')
        if self.signing_time and not self.signing_date:raise ValueError('填写签约时间时，请同时填写签约日期。')
        values=[self.bonus_min,self.bonus_target,self.bonus_max]
        if any(a>b for i,a in enumerate(values) if a is not None for b in values[i+1:] if b is not None):raise ValueError('浮动奖金需满足：低情景 ≤ 目标 ≤ 高情景。')
        if self.pay_quote_type == 'annual_range' and self.annual_reference_low is not None and self.annual_reference_high is not None and self.annual_reference_low > self.annual_reference_high:
            raise ValueError('参考年收入区间的下限不能高于上限。')
        if sum(phase.duration_months or 0 for phase in self.pay_phases if phase.included_in_first_year)>12:
            raise ValueError('纳入入职首年比较的阶段合计不能超过 12 个月，请调整月数或取消勾选毕业前的实习阶段。')
        dated=[phase for phase in self.pay_phases if phase.included_in_first_year and phase.start_date and phase.end_date]
        for index,phase in enumerate(dated):
            if any(phase.start_date < other.end_date and other.start_date < phase.end_date for other in dated[index+1:]):
                raise ValueError('纳入首年比较的阶段日期存在重叠，请核实见习期与试用期是否互相包含，避免工资重复计算。')
        return self


DETAIL_FIELDS={}
for group in SCHEMA['groups']:
    for field in group['fields']:
        if field['kind'] in {'money','number'}:
            DETAIL_FIELDS[field['key']]=(float|None,Field(default=None,ge=field.get('min',0),le=field.get('max',1_000_000_000),allow_inf_nan=False))
        else:
            DETAIL_FIELDS[field['key']]=(str,Field(default='',max_length=6000 if field['kind']=='textarea' else 800))
OfferDetails=create_model('OfferDetails',__base__=DetailsBase,**DETAIL_FIELDS)


class OfferCreate(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    company: str = Field(min_length=1,max_length=120)
    role: str = Field(min_length=1,max_length=160)
    city: str = Field(default='',max_length=120)
    opportunity_id: int|None = Field(default=None,gt=0)
    status: Literal['pending','negotiating','accepted','declined','withdrawn'] = 'pending'
    currency: Literal['CNY','USD','HKD','EUR','GBP','SGD','JPY'] = 'CNY'
    received_date: str = Field(default='',max_length=10)
    reply_deadline: str = Field(default='',max_length=10)
    start_date: str = Field(default='',max_length=10)
    details: OfferDetails = Field(default_factory=OfferDetails)

    @field_validator('received_date','reply_deadline','start_date')
    @classmethod
    def valid_date(cls,value):return check_date(value)


class OfferPatch(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    revision: int = Field(ge=1)
    company: str|None = Field(default=None,min_length=1,max_length=120)
    role: str|None = Field(default=None,min_length=1,max_length=160)
    city: str|None = Field(default=None,max_length=120)
    opportunity_id: int|None = Field(default=None,gt=0)
    status: Literal['pending','negotiating','accepted','declined','withdrawn']|None = None
    currency: Literal['CNY','USD','HKD','EUR','GBP','SGD','JPY']|None = None
    received_date: str|None = Field(default=None,max_length=10)
    reply_deadline: str|None = Field(default=None,max_length=10)
    start_date: str|None = Field(default=None,max_length=10)
    details: OfferDetails|None = None
    archived: bool|None = None


def attachment_rows(conn,offer_id):
    return [dict(row) for row in conn.execute('SELECT id,offer_id,name,mime_type,length(content) AS size,created_at FROM offer_attachments WHERE offer_id=? ORDER BY id',(offer_id,))]


def serialize(conn,row):
    item=dict(row);item['details']=json.loads(item['details']);item['archived']=bool(item['archived']);item['attachments']=attachment_rows(conn,item['id']);return item


def get_offer(offer_id):
    with db.connect() as conn:
        row=conn.execute('SELECT * FROM offers WHERE id=?',(offer_id,)).fetchone()
        return serialize(conn,row) if row else None


def register_routes(app: FastAPI):
    @app.get('/api/offers/schema')
    async def offer_schema():return SCHEMA

    @app.get('/api/offers')
    async def list_offers():
        with db.connect() as conn:
            return {'items':[serialize(conn,row) for row in conn.execute('SELECT * FROM offers ORDER BY created_at DESC,id DESC')]}

    @app.get('/api/offers/{offer_id}')
    async def read_offer(offer_id:int):
        item=get_offer(offer_id)
        if not item:raise HTTPException(404,'Offer 不存在。')
        return {'item':item}

    @app.post('/api/offers')
    async def create_offer(payload:OfferCreate):
        values=payload.model_dump()
        if values['opportunity_id'] and not db.get_opportunity(values['opportunity_id']):raise HTTPException(404,'关联岗位不存在。')
        values['details']=json.dumps(values['details'],ensure_ascii=False)
        with db.connect() as conn:
            cursor=conn.execute(f"INSERT INTO offers ({','.join(values)}) VALUES ({','.join('?' for _ in values)})",list(values.values()))
            offer_id=cursor.lastrowid
        return {'item':get_offer(offer_id)}

    @app.patch('/api/offers/{offer_id}')
    async def update_offer(offer_id:int,payload:OfferPatch):
        before=get_offer(offer_id)
        if not before:raise HTTPException(404,'Offer 不存在。')
        if payload.revision!=before['revision']:raise HTTPException(409,'这份 Offer 已在其他窗口更新。请保留当前输入，关闭后重新打开最新记录。')
        changes=payload.model_dump(exclude_unset=True);changes.pop('revision')
        merged={key:before[key] for key in OfferCreate.model_fields};merged.update({key:value for key,value in changes.items() if key!='archived'})
        # Validate the complete edited record so explicit nulls or invalid dates cannot corrupt it.
        try:validated=OfferCreate.model_validate(merged)
        except ValueError as exc:raise HTTPException(400,'填写内容不完整或格式错误，请核对日期、金额和公司岗位。') from exc
        if validated.opportunity_id and not db.get_opportunity(validated.opportunity_id):raise HTTPException(404,'关联岗位不存在。')
        if 'archived' in changes and changes['archived'] is None:raise HTTPException(400,'归档状态不能留空。')
        clean={key:validated.model_dump()[key] for key in changes if key!='archived'}
        if 'details' in clean:clean['details']=json.dumps(clean['details'],ensure_ascii=False)
        if 'archived' in changes:clean['archived']=int(changes['archived'])
        if not clean:return {'item':before}
        with db.connect() as conn:
            cursor=conn.execute(f"UPDATE offers SET {','.join(key+'=?' for key in clean)},revision=revision+1,updated_at=datetime('now','localtime') WHERE id=? AND revision=?",[*clean.values(),offer_id,payload.revision])
            if not cursor.rowcount:raise HTTPException(409,'Offer 已更新，请重新打开后保存。')
        return {'item':get_offer(offer_id)}

    @app.post('/api/offers/{offer_id}/attachments')
    async def upload_attachment(offer_id:int,file:UploadFile=File(...)):
        if not get_offer(offer_id):raise HTTPException(404,'Offer 不存在。')
        name=(file.filename or '附件').replace('\\','/').rsplit('/',1)[-1]
        name=''.join(c for c in name if ord(c)>=32)[:180] or '附件'
        types={'.pdf':'application/pdf','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','.txt':'text/plain'}
        mime=types.get(Path(name).suffix.lower())
        if not mime:raise HTTPException(400,'附件支持 PDF、图片、DOCX 或 TXT。')
        content=await file.read(10*1024*1024+1)
        if not content or len(content)>10*1024*1024:raise HTTPException(400,'附件不能为空，且不能超过 10MB。')
        with db.connect() as conn:
            if conn.execute('SELECT COUNT(*) FROM offer_attachments WHERE offer_id=?',(offer_id,)).fetchone()[0]>=20:raise HTTPException(400,'每份 Offer 最多保存 20 个附件。')
            conn.execute('INSERT INTO offer_attachments(offer_id,name,mime_type,content) VALUES(?,?,?,?)',(offer_id,name,mime,content))
            items=attachment_rows(conn,offer_id)
        return {'items':items}

    @app.get('/api/offers/{offer_id}/attachments/{attachment_id}')
    async def download_attachment(offer_id:int,attachment_id:int):
        with db.connect() as conn:
            row=conn.execute('SELECT * FROM offer_attachments WHERE id=? AND offer_id=?',(attachment_id,offer_id)).fetchone()
        if not row:raise HTTPException(404,'附件不存在。')
        return Response(row['content'],media_type=row['mime_type'],headers={'Content-Disposition':"attachment; filename*=UTF-8''"+quote(row['name'],safe=''),'X-Content-Type-Options':'nosniff','Cache-Control':'no-store'})
