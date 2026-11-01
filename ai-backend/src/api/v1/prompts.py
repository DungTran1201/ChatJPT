import uuid
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query, Request, UploadFile, File
from pydantic import BaseModel, Field, field_validator

from src.db import query_one, query_all, execute_commit
from src.core.security import get_optional_current_user
from src.services.text_import_service import (
    TextImportService,
    TextFileImportRequest
)

logger = logging.getLogger("system_prompts")

prompts_router = APIRouter(prefix="/system-prompts", tags=["Sensei Guidance & System Prompts"])

# ==============================================================================
# 1. PYDANTIC V2 SCHEMAS (SENSEI PERSONA SPECIFICATIONS)
# ==============================================================================

class SystemPromptCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Tên của Sensei (1-100 ký tự, e.g. Sakura-sensei 桜先生)"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Mô tả tóm tắt phong cách hoặc chuyên môn của Sensei (tối đa 500 ký tự)"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Chỉ thị Persona cốt lõi cho AI (System Prompt instructions, 1-10.000 ký tự)"
    )
    age: Optional[int] = Field(
        default=25,
        ge=18,
        le=100,
        description="Tuổi của Sensei (18-100)"
    )
    gender: Optional[str] = Field(
        default="female",
        description="Giới tính / Xưng hô của Sensei (female, male, other)"
    )
    japanese_level: Optional[str] = Field(
        default="N5",
        description="Trình độ tiếng Nhật chuyên trách (N5, N4, N3, N2, N1, ALL)"
    )
    personality: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Nét tính cách sư phạm đặc trưng (e.g. Dịu dàng, Kiên nhẫn, Hóm hỉnh)"
    )
    teaching_style: Optional[str] = Field(
        default=None,
        description="Phương pháp sư phạm & quy chuẩn Furigana/Song ngữ"
    )
    catchphrase: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Câu nói cửa miệng / Lời chào thương hiệu của Sensei"
    )
    hobbies: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Sở thích & chủ đề đàm thoại yêu thích của Sensei"
    )
    avatar_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Ảnh đại diện Sensei (Avatar URL)"
    )
    is_default: Optional[bool] = Field(
        default=False,
        description="Đặt làm Sensei mặc định đồng hành"
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Tên Sensei không được để trống hoặc chỉ chứa khoảng trắng.")
        return trimmed

    @field_validator("content")
    @classmethod
    def validate_content_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Nội dung chỉ dẫn Persona không được để trống hoặc chỉ chứa khoảng trắng.")
        return v

    @field_validator("description", "personality", "teaching_style", "catchphrase", "hobbies", "avatar_url")
    @classmethod
    def sanitize_optional_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None


class SystemPromptUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    content: str = Field(..., min_length=1, max_length=10000)
    age: Optional[int] = Field(default=25, ge=18, le=100)
    gender: Optional[str] = Field(default="female")
    japanese_level: Optional[str] = Field(default="N5")
    personality: Optional[str] = Field(default=None, max_length=255)
    teaching_style: Optional[str] = Field(default=None)
    catchphrase: Optional[str] = Field(default=None, max_length=255)
    hobbies: Optional[str] = Field(default=None, max_length=255)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    is_default: Optional[bool] = Field(default=False)

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Tên Sensei không được để trống hoặc chỉ chứa khoảng trắng.")
        return trimmed

    @field_validator("content")
    @classmethod
    def validate_content_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Nội dung chỉ dẫn Persona không được để trống hoặc chỉ chứa khoảng trắng.")
        return v


class SystemPromptSummaryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    content_length: int
    age: Optional[int] = 25
    gender: Optional[str] = "female"
    japanese_level: Optional[str] = "N5"
    personality: Optional[str] = None
    teaching_style: Optional[str] = None
    catchphrase: Optional[str] = None
    hobbies: Optional[str] = None
    avatar_url: Optional[str] = None
    is_default: bool = False
    is_system_preset: bool = False
    created_at: str
    updated_at: str


class SystemPromptListResponse(BaseModel):
    items: List[SystemPromptSummaryResponse]
    total: int


class SystemPromptDetailResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    content: str
    age: Optional[int] = 25
    gender: Optional[str] = "female"
    japanese_level: Optional[str] = "N5"
    personality: Optional[str] = None
    teaching_style: Optional[str] = None
    catchphrase: Optional[str] = None
    hobbies: Optional[str] = None
    avatar_url: Optional[str] = None
    is_default: bool = False
    is_system_preset: bool = False
    attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    created_at: str
    updated_at: str


# ==============================================================================
# 2. CONTROLLER ENDPOINTS
# ==============================================================================

@prompts_router.get("", response_model=SystemPromptListResponse)
async def list_system_prompts(
    q: Optional[str] = Query(None, description="Từ khóa tìm kiếm lọc theo tên, mô tả hoặc tính cách Sensei"),
    level: Optional[str] = Query(None, description="Lọc theo trình độ JLPT (N5, N4, N3, N2, N1, ALL)"),
    sort: str = Query("level_asc", description="Thứ tự sắp xếp: level_asc, updated_desc, name_asc"),
    current_user: dict = Depends(get_optional_current_user)
):
    """
    Lấy danh sách Sensei thuộc quyền sở hữu của người dùng hiện tại HOẶC các Sensei mẫu hệ thống (is_system_preset = 1).
    Hỗ trợ tìm kiếm từ khóa và lọc theo trình độ JLPT N5 đến N1.
    """
    user_id = current_user.get("id", "guest_user")

    sort_clauses = {
        "level_asc": "CASE japanese_level WHEN 'N5' THEN 1 WHEN 'N4' THEN 2 WHEN 'N3' THEN 3 WHEN 'N2' THEN 4 WHEN 'N1' THEN 5 ELSE 6 END, updated_at DESC",
        "updated_desc": "updated_at DESC",
        "name_asc": "name COLLATE NOCASE ASC",
        "length_desc": "LENGTH(content) DESC",
    }
    order_by = sort_clauses.get(sort, sort_clauses["level_asc"])

    conditions = ["(user_id = ? OR is_system_preset = 1)"]
    params: List[Any] = [user_id]

    if level and level.upper() != "ALL":
        conditions.append("japanese_level = ?")
        params.append(level.upper())

    if q and q.strip():
        search_pattern = f"%{q.strip()}%"
        conditions.append("(name LIKE ? OR description LIKE ? OR personality LIKE ? OR teaching_style LIKE ?)")
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    where_clause = " AND ".join(conditions)
    sql = f"""
        SELECT id, name, description, LENGTH(content) AS content_length,
               age, gender, japanese_level, personality, teaching_style, catchphrase,
               hobbies, avatar_url, is_default, is_system_preset, created_at, updated_at
        FROM system_prompts
        WHERE {where_clause}
        ORDER BY {order_by}
    """
    rows = query_all(sql, tuple(params))

    items = [
        SystemPromptSummaryResponse(
            id=r["id"],
            name=r["name"],
            description=r.get("description"),
            content_length=r.get("content_length", 0),
            age=r.get("age", 25),
            gender=r.get("gender", "female"),
            japanese_level=r.get("japanese_level", "N5"),
            personality=r.get("personality"),
            teaching_style=r.get("teaching_style"),
            catchphrase=r.get("catchphrase"),
            hobbies=r.get("hobbies"),
            avatar_url=r.get("avatar_url") or f"https://api.dicebear.com/7.x/bottts/svg?seed={r['id']}",
            is_default=bool(r.get("is_default", 0)),
            is_system_preset=bool(r.get("is_system_preset", 0)),
            created_at=str(r.get("created_at")),
            updated_at=str(r.get("updated_at"))
        )
        for r in rows
    ]

    return SystemPromptListResponse(items=items, total=len(items))


@prompts_router.post("", response_model=SystemPromptDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_system_prompt(
    payload: SystemPromptCreateRequest,
    current_user: dict = Depends(get_optional_current_user)
):
    """Tạo mới một Sensei trong thư viện của người dùng."""
    user_id = current_user.get("id", "guest_user")
    name = payload.name.strip()

    # Kiểm tra trùng tên đối với user_id
    existing = query_one(
        "SELECT id FROM system_prompts WHERE user_id = ? AND LOWER(name) = LOWER(?)",
        (user_id, name)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "PROMPT_NAME_CONFLICT",
                "message": "Bạn đã có một Sensei mang tên này. Vui lòng chọn tên khác."
            }
        )

    prompt_id = f"sp_{uuid.uuid4().hex}"
    avatar = payload.avatar_url or f"https://api.dicebear.com/7.x/bottts/svg?seed={prompt_id}"

    # Nếu đặt is_default, bỏ default của các Sensei khác của user
    if payload.is_default:
        execute_commit("UPDATE system_prompts SET is_default = 0 WHERE user_id = ?", (user_id,))

    execute_commit(
        """
        INSERT INTO system_prompts (
            id, user_id, name, description, content, age, gender, japanese_level,
            personality, teaching_style, catchphrase, hobbies, avatar_url,
            is_default, is_system_preset, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
        """,
        (
            prompt_id, user_id, name, payload.description, payload.content,
            payload.age or 25, payload.gender or "female", payload.japanese_level or "N5",
            payload.personality, payload.teaching_style, payload.catchphrase,
            payload.hobbies, avatar, int(bool(payload.is_default))
        )
    )

    row = query_one(
        "SELECT * FROM system_prompts WHERE id = ?",
        (prompt_id,)
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "DB_INSERT_FAILED", "message": "Không thể lưu Sensei vào cơ sở dữ liệu."}
        )

    logger.info("Tạo Sensei thành công: id=%s, user_id=%s, name='%s'", prompt_id, user_id, name)

    return SystemPromptDetailResponse(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        description=row.get("description"),
        content=row["content"],
        age=row.get("age", 25),
        gender=row.get("gender", "female"),
        japanese_level=row.get("japanese_level", "N5"),
        personality=row.get("personality"),
        teaching_style=row.get("teaching_style"),
        catchphrase=row.get("catchphrase"),
        hobbies=row.get("hobbies"),
        avatar_url=row.get("avatar_url") or avatar,
        is_default=bool(row.get("is_default", 0)),
        is_system_preset=bool(row.get("is_system_preset", 0)),
        created_at=str(row.get("created_at")),
        updated_at=str(row.get("updated_at"))
    )


@prompts_router.get("/{id}", response_model=SystemPromptDetailResponse)
async def get_system_prompt_detail(
    id: str,
    current_user: dict = Depends(get_optional_current_user)
):
    """Lấy thông tin chi tiết của Sensei (hỗ trợ cả Sensei sở hữu và Sensei hệ thống)."""
    user_id = current_user.get("id", "guest_user")

    row = query_one(
        "SELECT * FROM system_prompts WHERE id = ? AND (user_id = ? OR is_system_preset = 1)",
        (id, user_id)
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "PROMPT_NOT_FOUND",
                "message": "Sensei không tồn tại hoặc bạn không có quyền truy cập."
            }
        )

    atts = query_all(
        "SELECT id, filename, mime_type, file_size, status, created_at FROM attachments WHERE prompt_id = ? ORDER BY created_at DESC",
        (id,)
    )

    return SystemPromptDetailResponse(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        description=row.get("description"),
        content=row["content"],
        age=row.get("age", 25),
        gender=row.get("gender", "female"),
        japanese_level=row.get("japanese_level", "N5"),
        personality=row.get("personality"),
        teaching_style=row.get("teaching_style"),
        catchphrase=row.get("catchphrase"),
        hobbies=row.get("hobbies"),
        avatar_url=row.get("avatar_url") or f"https://api.dicebear.com/7.x/bottts/svg?seed={row['id']}",
        is_default=bool(row.get("is_default", 0)),
        is_system_preset=bool(row.get("is_system_preset", 0)),
        attachments=atts,
        created_at=str(row.get("created_at")),
        updated_at=str(row.get("updated_at"))
    )


@prompts_router.put("/{id}", response_model=SystemPromptDetailResponse)
async def update_system_prompt(
    id: str,
    payload: SystemPromptUpdateRequest,
    current_user: dict = Depends(get_optional_current_user)
):
    """Cập nhật thông tin chi tiết của Sensei."""
    user_id = current_user.get("id", "guest_user")
    name = payload.name.strip()

    existing = query_one(
        "SELECT * FROM system_prompts WHERE id = ? AND (user_id = ? OR is_system_preset = 1)",
        (id, user_id)
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "PROMPT_NOT_FOUND", "message": "Sensei không tồn tại hoặc bạn không có quyền truy cập."}
        )

    # Kiểm tra trùng tên đối với user_id
    duplicate = query_one(
        "SELECT id FROM system_prompts WHERE user_id = ? AND LOWER(name) = LOWER(?) AND id != ?",
        (user_id, name, id)
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "PROMPT_NAME_CONFLICT",
                "message": "Bạn đã có một Sensei khác mang tên này. Vui lòng chọn tên khác."
            }
        )

    # Nếu sửa Sensei hệ thống, tạo bản ghi tùy chỉnh cho user
    target_id = id
    if existing.get("is_system_preset"):
        target_id = f"sp_custom_{uuid.uuid4().hex[:12]}"
        execute_commit(
            """
            INSERT INTO system_prompts (
                id, user_id, name, description, content, age, gender, japanese_level,
                personality, teaching_style, catchphrase, hobbies, avatar_url,
                is_default, is_system_preset, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
            """,
            (
                target_id, user_id, name, payload.description, payload.content,
                payload.age or existing.get("age", 25),
                payload.gender or existing.get("gender", "female"),
                payload.japanese_level or existing.get("japanese_level", "N5"),
                payload.personality, payload.teaching_style, payload.catchphrase,
                payload.hobbies, payload.avatar_url or existing.get("avatar_url"),
                int(bool(payload.is_default))
            )
        )
    else:
        execute_commit(
            """
            UPDATE system_prompts
            SET name = ?, description = ?, content = ?, age = ?, gender = ?,
                japanese_level = ?, personality = ?, teaching_style = ?,
                catchphrase = ?, hobbies = ?, avatar_url = ?, is_default = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (
                name, payload.description, payload.content,
                payload.age or 25, payload.gender or "female",
                payload.japanese_level or "N5", payload.personality,
                payload.teaching_style, payload.catchphrase, payload.hobbies,
                payload.avatar_url, int(bool(payload.is_default)),
                target_id, user_id
            )
        )

    row = query_one("SELECT * FROM system_prompts WHERE id = ?", (target_id,))

    return SystemPromptDetailResponse(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        description=row.get("description"),
        content=row["content"],
        age=row.get("age", 25),
        gender=row.get("gender", "female"),
        japanese_level=row.get("japanese_level", "N5"),
        personality=row.get("personality"),
        teaching_style=row.get("teaching_style"),
        catchphrase=row.get("catchphrase"),
        hobbies=row.get("hobbies"),
        avatar_url=row.get("avatar_url"),
        is_default=bool(row.get("is_default", 0)),
        is_system_preset=bool(row.get("is_system_preset", 0)),
        created_at=str(row.get("created_at")),
        updated_at=str(row.get("updated_at"))
    )


@prompts_router.delete("/{id}")
async def delete_system_prompt(
    id: str,
    current_user: dict = Depends(get_optional_current_user)
):
    """Xóa Sensei cá nhân (Không cho phép xóa Sensei mặc định hệ thống)."""
    user_id = current_user.get("id", "guest_user")

    existing = query_one(
        "SELECT id, is_system_preset FROM system_prompts WHERE id = ? AND (user_id = ? OR is_system_preset = 1)",
        (id, user_id)
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "PROMPT_NOT_FOUND", "message": "Sensei không tồn tại hoặc bạn không có quyền truy cập."}
        )

    if existing.get("is_system_preset"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "CANNOT_DELETE_PRESET", "message": "Không thể xóa Sensei mẫu được bảo vệ của hệ thống."}
        )

    execute_commit("DELETE FROM system_prompts WHERE id = ? AND user_id = ?", (id, user_id))

    return {"success": True, "message": "Đã xóa Sensei thành công.", "deleted_id": id}


@prompts_router.post("/{id}/clone", response_model=SystemPromptDetailResponse, status_code=status.HTTP_201_CREATED)
async def clone_system_prompt(
    id: str,
    current_user: dict = Depends(get_optional_current_user)
):
    """Nhân bản Sensei (tạo một Sensei mới để học viên tự do tùy chỉnh)."""
    user_id = current_user.get("id", "guest_user")

    origin = query_one(
        "SELECT * FROM system_prompts WHERE id = ? AND (user_id = ? OR is_system_preset = 1)",
        (id, user_id)
    )
    if not origin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "PROMPT_NOT_FOUND", "message": "Sensei không tồn tại hoặc bạn không có quyền truy cập."}
        )

    base_name = origin["name"]
    clone_name = f"{base_name} (Copy)"
    if len(clone_name) > 100:
        base_name = base_name[: 100 - len(" (Copy)")]
        clone_name = f"{base_name} (Copy)"

    counter = 1
    while True:
        existing = query_one(
            "SELECT id FROM system_prompts WHERE user_id = ? AND LOWER(name) = LOWER(?)",
            (user_id, clone_name)
        )
        if not existing:
            break
        counter += 1
        suffix = f" (Copy {counter})"
        trimmed_base = base_name[: 100 - len(suffix)]
        clone_name = f"{trimmed_base}{suffix}"

    new_id = f"sp_{uuid.uuid4().hex}"
    execute_commit(
        """
        INSERT INTO system_prompts (
            id, user_id, name, description, content, age, gender, japanese_level,
            personality, teaching_style, catchphrase, hobbies, avatar_url,
            is_default, is_system_preset, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, CURRENT_TIMESTAMP)
        """,
        (
            new_id, user_id, clone_name, origin.get("description"), origin["content"],
            origin.get("age", 25), origin.get("gender", "female"),
            origin.get("japanese_level", "N5"), origin.get("personality"),
            origin.get("teaching_style"), origin.get("catchphrase"),
            origin.get("hobbies"), origin.get("avatar_url")
        )
    )

    row = query_one("SELECT * FROM system_prompts WHERE id = ?", (new_id,))

    return SystemPromptDetailResponse(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        description=row.get("description"),
        content=row["content"],
        age=row.get("age", 25),
        gender=row.get("gender", "female"),
        japanese_level=row.get("japanese_level", "N5"),
        personality=row.get("personality"),
        teaching_style=row.get("teaching_style"),
        catchphrase=row.get("catchphrase"),
        hobbies=row.get("hobbies"),
        avatar_url=row.get("avatar_url"),
        is_default=bool(row.get("is_default", 0)),
        is_system_preset=False,
        created_at=str(row.get("created_at")),
        updated_at=str(row.get("updated_at"))
    )


@prompts_router.post("/import-file", response_model=SystemPromptDetailResponse, status_code=status.HTTP_201_CREATED)
async def import_system_prompt_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_optional_current_user)
):
    """Nhập thông tin Sensei từ tệp văn bản tải lên."""
    user_id = current_user.get("id", "guest_user")
    filename = file.filename or "untitled.txt"
    content_bytes = await file.read()
    text = TextImportService.validate_and_decode_bytes(filename, content_bytes)
    res = TextImportService.import_system_prompt(user_id=user_id, filename=filename, content=text)
    return SystemPromptDetailResponse(**res)


@prompts_router.post("/import-text", response_model=SystemPromptDetailResponse, status_code=status.HTTP_201_CREATED)
async def import_system_prompt_text(
    req: TextFileImportRequest,
    current_user: dict = Depends(get_optional_current_user)
):
    """Nhập thông tin Sensei từ nội dung văn bản."""
    user_id = current_user.get("id", "guest_user")
    text = TextImportService.validate_and_decode_bytes(req.filename, req.content.encode("utf-8"))
    res = TextImportService.import_system_prompt(
        user_id=user_id,
        filename=req.filename,
        content=text,
        override_name=req.name,
        override_desc=req.description
    )
    return SystemPromptDetailResponse(**res)
