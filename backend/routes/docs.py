"""
知识文档接口:列表/详情/新增/编辑/删除/分类列表
- 查询(GET)无需登录,方便分享只读链接
- 写操作(POST/PUT/DELETE)需登录
"""
from flask import Blueprint, request, jsonify

from db import get_conn
from auth import login_required

bp = Blueprint("docs", __name__, url_prefix="/api/docs")


def _make_summary(content: str, n: int = 120) -> str:
    """从 Markdown 截取纯文本摘要(去掉常见 MD 符号)"""
    if not content:
        return ""
    text = content.replace("\n", " ").replace("#", "").replace("*", "").replace("`", "")
    text = " ".join(text.split())
    return text[:n]


@bp.get("")
def list_docs():
    """
    GET /api/docs?keyword=&category=&page=1&page_size=20
    模糊搜索 title/content/category;keyword 为空则不过滤。
    """
    keyword = (request.args.get("keyword") or "").strip()
    category = (request.args.get("category") or "").strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
        page_size = min(100, max(1, int(request.args.get("page_size", 20))))
    except ValueError:
        page, page_size = 1, 20

    where = []
    params: list = []
    if keyword:
        kw = f"%{keyword}%"
        where.append("(title LIKE ? OR content LIKE ? OR category LIKE ?)")
        params += [kw, kw, kw]
    if category:
        where.append("category = ?")
        params.append(category)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = get_conn()
    total = conn.execute(
        f"SELECT COUNT(*) AS n FROM documents {where_sql}", params
    ).fetchone()["n"]
    rows = conn.execute(
        f"""SELECT id, title, category, summary, created_at, updated_at
            FROM documents {where_sql}
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?""",
        params + [page_size, (page - 1) * page_size],
    ).fetchall()
    return jsonify(
        code=0,
        msg="ok",
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [dict(r) for r in rows],
        },
    )


@bp.get("/categories")
def list_categories():
    """GET /api/docs/categories  返回去重后的分类列表(含数量)"""
    rows = get_conn().execute(
        """SELECT category, COUNT(*) AS n FROM documents
           GROUP BY category ORDER BY n DESC"""
    ).fetchall()
    return jsonify(code=0, msg="ok", data=[dict(r) for r in rows])


@bp.get("/<int:doc_id>")
def get_doc(doc_id: int):
    """GET /api/docs/<id>  详情"""
    row = get_conn().execute(
        "SELECT * FROM documents WHERE id=?", (doc_id,)
    ).fetchone()
    if not row:
        return jsonify(code=404, msg="文档不存在"), 404
    return jsonify(code=0, msg="ok", data=dict(row))


@bp.post("")
@login_required
def create_doc():
    """POST /api/docs  body: {title, category, content}"""
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify(code=400, msg="标题不能为空"), 400
    category = (data.get("category") or "默认").strip() or "默认"
    content = data.get("content") or ""
    summary = _make_summary(content)

    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO documents(title, category, content, summary)
           VALUES(?,?,?,?)""",
        (title, category, content, summary),
    )
    conn.commit()
    return jsonify(code=0, msg="ok", data={"id": cur.lastrowid})


@bp.put("/<int:doc_id>")
@login_required
def update_doc(doc_id: int):
    """PUT /api/docs/<id>  全字段更新"""
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify(code=400, msg="标题不能为空"), 400
    category = (data.get("category") or "默认").strip() or "默认"
    content = data.get("content") or ""
    summary = _make_summary(content)

    conn = get_conn()
    res = conn.execute(
        """UPDATE documents
           SET title=?, category=?, content=?, summary=?, updated_at=CURRENT_TIMESTAMP
           WHERE id=?""",
        (title, category, content, summary, doc_id),
    )
    conn.commit()
    if res.rowcount == 0:
        return jsonify(code=404, msg="文档不存在"), 404
    return jsonify(code=0, msg="ok")


@bp.delete("/<int:doc_id>")
@login_required
def delete_doc(doc_id: int):
    """DELETE /api/docs/<id>"""
    conn = get_conn()
    res = conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    conn.commit()
    if res.rowcount == 0:
        return jsonify(code=404, msg="文档不存在"), 404
    return jsonify(code=0, msg="ok")
